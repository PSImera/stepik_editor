"""Сценарий загрузки структуры курса (модули, уроки, описание) в Stepik."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .api import StepikAPIClient


def _confirm(prompt: str) -> bool:
    """Запрашивает Y/n в консоли. Возвращает True для Y/y/Enter, False для n/N."""
    while True:
        answer = input(f"{prompt} [Y/n] ").strip().lower()
        if answer in ("", "y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("  Please enter Y or n.")


# Поля описания курса, которые синхронизируются с Stepik
_LESSON_TITLE_MAX_LEN = 64
_SECTION_TITLE_MAX_LEN = 100

_COURSE_DESCRIPTION_FIELDS = (
    "title",
    "summary",
    "description",
    "target_audience",
    "requirements",
    "workload",
    "certificate",
    "intro",
    "course_format",
    "learning_format",
    "acquired_skills",
    "acquired_assets",
)


class StructureUploadMixin:
    if TYPE_CHECKING:
        client: StepikAPIClient
        course_id: int
        course_info: dict[str, Any]
        structure: list[dict[str, Any]]

        def _save_course_data(self) -> None: ...

    def upload_structure(self, *, dry_run: bool = False, sync_deletions: bool = False) -> None:
        """Синхронизирует описание курса, модули и уроки из локального structure.json в Stepik.

        Создаёт модули и уроки, которых нет на сайте.
        Переименовывает существующие, если название изменилось.
        sync_deletions=True — дополнительно предлагает удалить модули и уроки,
        которые есть на Stepik, но отсутствуют в локальном structure.json.
        """
        mode = "dry-run" if dry_run else "upload"
        print(f"\n=== upload_structure ({mode}) ===")
        self._sync_course_metadata(dry_run=dry_run)
        self._sync_sections(dry_run=dry_run, sync_deletions=sync_deletions)
        print("=== upload_structure done ===\n")

    # ------------------------------------------------------------------
    # Описание курса
    # ------------------------------------------------------------------

    def _sync_course_metadata(self, *, dry_run: bool) -> None:
        local = self.course_info
        remote = self.client.get_course(self.course_id)

        changed = {
            k: local[k]
            for k in _COURSE_DESCRIPTION_FIELDS
            if k in local and local.get(k) != remote.get(k)
        }

        if not changed:
            print("Course metadata: no changes")
            return

        print(f"Course metadata: updating {list(changed.keys())}")
        if not dry_run:
            # Stepik требует title в каждом PUT-запросе курса
            payload = {"title": local.get("title") or remote.get("title", ""), **changed}
            self.client.update_course(self.course_id, payload)

    # ------------------------------------------------------------------
    # Секции (модули)
    # ------------------------------------------------------------------

    def _sync_sections(self, *, dry_run: bool, sync_deletions: bool = False) -> None:
        for local_sec in self.structure:
            section_id = local_sec.get("section_id") or 0
            title = local_sec["section_title"]
            position = local_sec["section_position"]

            if len(title) > _SECTION_TITLE_MAX_LEN:
                print(f"  Module {position}: SKIP — title too long ({len(title)} > {_SECTION_TITLE_MAX_LEN}): '{title}'")
                continue

            if section_id:
                remote_title = local_sec.get("section_info", {}).get("title", "")
                if title != remote_title:
                    print(f"  Module {position}: rename '{remote_title}' → '{title}'")
                    if not dry_run:
                        self.client.update_section(section_id, {"title": title, "position": position})
                        local_sec.setdefault("section_info", {})["title"] = title
                        self._save_course_data()
                else:
                    print(f"  Module {position}: '{title}' — up to date")
            else:
                print(f"  Module {position}: create '{title}'")
                if not dry_run:
                    created = self.client.create_section(self.course_id, title, position)
                    section_id = created.get("id", 0)
                    if not section_id:
                        print(f"    ERROR: Stepik did not return section id")
                        continue
                    local_sec["section_id"] = section_id
                    local_sec["section_info"] = created
                    self._save_course_data()

            if section_id:
                self._sync_lessons(local_sec, section_id, dry_run=dry_run, sync_deletions=sync_deletions)

        if sync_deletions:
            self._delete_orphaned_sections(dry_run=dry_run)

    def _delete_orphaned_sections(self, *, dry_run: bool) -> None:
        remote_course = self.client.get_course(self.course_id)
        remote_section_ids: list[int] = remote_course.get("sections", [])
        local_section_ids: set[int] = {
            s["section_id"] for s in self.structure if s.get("section_id")
        }
        orphaned = [sid for sid in remote_section_ids if sid not in local_section_ids]
        if not orphaned:
            return
        for sid in orphaned:
            section_info = self.client.get_section(sid)
            title = section_info.get("title", f"id={sid}")
            confirmed = _confirm(f"  Delete module '{title}' (id={sid}) from Stepik?")
            if confirmed:
                print(f"  Module '{title}': deleting")
                if not dry_run:
                    self.client.delete_section(sid)
            else:
                print(f"  Module '{title}': skipped")

    # ------------------------------------------------------------------
    # Уроки внутри секции
    # ------------------------------------------------------------------

    def _sync_lessons(
        self, local_sec: dict[str, Any], section_id: int, *, dry_run: bool, sync_deletions: bool = False
    ) -> None:
        for lesson_entry in local_sec.get("lessons", []):
            lesson_id = lesson_entry.get("lesson_id") or 0
            unit_id = lesson_entry.get("unit_id") or 0
            title = lesson_entry["lesson_title"]
            position = lesson_entry["position"]

            if len(title) > _LESSON_TITLE_MAX_LEN:
                print(f"    Lesson {position}: SKIP — title too long ({len(title)} > {_LESSON_TITLE_MAX_LEN}): '{title}'")
                continue

            if lesson_id == 0:
                # черновик — создаём урок и unit
                print(f"    Lesson {position}: create '{title}'")
                if not dry_run:
                    created_lesson = self.client.create_lesson(title)
                    lesson_id = created_lesson.get("id", 0)
                    if not lesson_id:
                        print(f"      ERROR: Stepik did not return lesson id")
                        continue
                    created_unit = self.client.create_unit(section_id, lesson_id, position)
                    unit_id = created_unit.get("id", 0)
                    lesson_entry["lesson_id"] = lesson_id
                    lesson_entry["unit_id"] = unit_id
                    lesson_entry["lesson_info"] = created_lesson
                    lesson_entry["unit_info"] = created_unit
                    self._save_course_data()
                continue

            # урок существует — проверяем название
            remote_title = lesson_entry.get("lesson_info", {}).get("title", "")
            if title != remote_title:
                print(f"    Lesson {position}: rename '{remote_title}' → '{title}'")
                if not dry_run:
                    self.client.update_lesson(lesson_id, title)
                    lesson_entry.setdefault("lesson_info", {})["title"] = title
                    self._save_course_data()
            else:
                print(f"    Lesson {position}: '{title}' — up to date")

            # unit может отсутствовать (урок есть, но не привязан к секции)
            if not unit_id:
                print(f"    Lesson {position}: create unit")
                if not dry_run:
                    created_unit = self.client.create_unit(section_id, lesson_id, position)
                    unit_id = created_unit.get("id", 0)
                    lesson_entry["unit_id"] = unit_id
                    lesson_entry["unit_info"] = created_unit
                    self._save_course_data()

        if sync_deletions:
            self._delete_orphaned_lessons(local_sec, section_id, dry_run=dry_run)

    def _delete_orphaned_lessons(
        self, local_sec: dict[str, Any], section_id: int, *, dry_run: bool
    ) -> None:
        section_info = self.client.get_section(section_id)
        remote_unit_ids: list[int] = section_info.get("units", [])
        local_lesson_ids: set[int] = {
            e["lesson_id"] for e in local_sec.get("lessons", []) if e.get("lesson_id")
        }
        for unit_id in remote_unit_ids:
            unit = self.client.get_unit(unit_id)
            lesson_id = unit.get("lesson", 0)
            if lesson_id and lesson_id not in local_lesson_ids:
                lesson_info = self.client.get_lesson(lesson_id)
                title = lesson_info.get("title", f"id={lesson_id}")
                confirmed = _confirm(
                    f"    Delete lesson '{title}' (lesson_id={lesson_id}, unit_id={unit_id})?"
                )
                if confirmed:
                    print(f"    Lesson '{title}': deleting unit")
                    if not dry_run:
                        self.client.delete_unit(unit_id)
                else:
                    print(f"    Lesson '{title}': skipped")
