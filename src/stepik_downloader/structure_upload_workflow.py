"""Сценарий загрузки структуры курса (модули, уроки, описание) в Stepik."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .api import StepikAPIClient


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

    def upload_structure(self, *, dry_run: bool = False) -> None:
        """Синхронизирует описание курса, модули и уроки из локального structure.json в Stepik.

        Создаёт модули и уроки, которых нет на сайте.
        Переименовывает существующие, если название изменилось.
        Не удаляет ничего на Stepik.
        """
        mode = "dry-run" if dry_run else "upload"
        print(f"\n=== upload_structure ({mode}) ===")
        self._sync_course_metadata(dry_run=dry_run)
        self._sync_sections(dry_run=dry_run)
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

    def _sync_sections(self, *, dry_run: bool) -> None:
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
                self._sync_lessons(local_sec, section_id, dry_run=dry_run)

    # ------------------------------------------------------------------
    # Уроки внутри секции
    # ------------------------------------------------------------------

    def _sync_lessons(
        self, local_sec: dict[str, Any], section_id: int, *, dry_run: bool
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
