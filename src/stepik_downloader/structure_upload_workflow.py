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
                self._ensure_unit_positions(local_sec, section_id, dry_run=dry_run)

        self._ensure_section_positions(dry_run=dry_run)

        if sync_deletions:
            self._delete_orphaned_sections(dry_run=dry_run)

    def _ensure_section_positions(self, *, dry_run: bool) -> None:
        """Сверяет позиции секций (модулей) с порядком в structure.json и чинит расхождения.

        `_sync_sections` отправляет позицию секции на Stepik только вместе с
        переименованием. Если модуль переставили (изменилась позиция, а название —
        нет), ветка «up to date» не трогает позицию, и порядок модулей на сайте
        расходится с structure.json. Двухфазный алгоритм, как в `_ensure_unit_positions`:
        1. Паркует неверно расположенные секции на временные позиции (>> max).
        2. Ставит каждую секцию на целевую позицию (от меньшей к большей).
        """
        managed = [s for s in self.structure if s.get("section_id")]
        target: dict[int, int] = {s["section_id"]: s["section_position"] for s in managed}
        if not target:
            return

        # Берём секции через get_course + get_section поштучно: фильтр /api/sections?course=
        # возвращает пустой список (как и /api/units?section=), поэтому полагаться на него
        # нельзя — иначе сверка молча решает, что «всё верно». Этот путь надёжен.
        remote_course = self.client.get_course(self.course_id)
        current_sections = [
            s for sid in remote_course.get("sections", []) if (s := self.client.get_section(sid))
        ]
        current_pos: dict[int, int] = {
            s["id"]: s["position"] for s in current_sections if s["id"] in target
        }

        misplaced: dict[int, tuple[int, int]] = {
            sid: (current_pos[sid], tgt)
            for sid, tgt in target.items()
            if sid in current_pos and current_pos[sid] != tgt
        }

        if not misplaced:
            print("  Section positions: all correct")
            return

        for sid, (cur, tgt) in misplaced.items():
            print(f"  Section position mismatch: section {sid}: Stepik={cur}, expected={tgt}")

        if dry_run:
            for sid, (_, tgt) in misplaced.items():
                print(f"  will fix section {sid} → {tgt}")
            return

        title_by_id: dict[int, str] = {s["section_id"]: s["section_title"] for s in managed}
        max_pos = max((s["position"] for s in current_sections), default=0)

        # Phase 1: паркуем неверные секции на временные позиции (>> max)
        temp_positions: dict[int, int] = {}
        for i, sid in enumerate(misplaced):
            temp_pos = max_pos + 100 + i
            try:
                self.client.update_section(sid, {"title": title_by_id[sid], "position": temp_pos})
                temp_positions[sid] = temp_pos
                print(f"    section {sid}: parked at {temp_pos}")
            except Exception as exc:
                print(f"    section {sid}: failed to park: {exc}")

        # Phase 2: ставим каждую секцию на целевую позицию (от меньшей к большей)
        for sid, (_, target_pos) in sorted(misplaced.items(), key=lambda kv: kv[1][1]):
            if sid not in temp_positions:
                continue
            try:
                self.client.update_section(sid, {"title": title_by_id[sid], "position": target_pos})
                print(f"    section {sid}: moved → {target_pos}")
            except Exception as exc:
                print(f"    section {sid}: failed to move to {target_pos}: {exc}")

        # Обновляем локальные section_info.position, чтобы structure.json отражал новый порядок
        for entry in managed:
            if entry["section_id"] in target:
                entry.setdefault("section_info", {})["position"] = entry["section_position"]
        self._save_course_data()

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

    def _ensure_unit_positions(
        self, local_sec: dict[str, Any], section_id: int, *, dry_run: bool
    ) -> None:
        """Сверяет позиции units секции с порядком уроков в structure.json и чинит расхождения.

        `_sync_lessons` переименовывает уроки и создаёт недостающие units, но никогда не
        переставляет уже существующие. Без этой сверки порядок уроков на сайте расходится
        с локальным structure.json — например, после вставки нового урока в середину модуля
        соседние уроки на сайте остаются в старом порядке.

        Алгоритм двухфазный, как в `_ensure_step_positions`, чтобы избежать конфликтов позиций:
        1. Паркует неверно расположенные units на временные позиции (>> max).
        2. Ставит каждый unit на целевую позицию из structure.json (от меньшей к большей).
        """
        managed = [e for e in local_sec.get("lessons", []) if e.get("unit_id")]
        target: dict[int, int] = {e["unit_id"]: e["position"] for e in managed}
        if not target:
            return

        # Берём units через get_section + get_unit поштучно: фильтр /api/units?section=
        # отвечает крайне медленно и упирается в таймаут, а этот путь надёжен (его же
        # использует загрузчик при скачивании структуры).
        section_info = self.client.get_section(section_id)
        current_units = [
            u for uid in section_info.get("units", []) if (u := self.client.get_unit(uid))
        ]
        current_pos: dict[int, int] = {u["id"]: u["position"] for u in current_units}
        lesson_by_unit: dict[int, int] = {u["id"]: u["lesson"] for u in current_units}

        misplaced: dict[int, tuple[int, int]] = {
            uid: (current_pos[uid], tgt)
            for uid, tgt in target.items()
            if uid in current_pos and current_pos[uid] != tgt
        }

        if not misplaced:
            print("    Unit positions: all correct")
            return

        for uid, (cur, tgt) in misplaced.items():
            print(f"    Unit position mismatch: unit {uid}: Stepik={cur}, expected={tgt}")

        if dry_run:
            for uid, (_, tgt) in misplaced.items():
                print(f"    will fix unit {uid} → {tgt}")
            return

        max_pos = max((u["position"] for u in current_units), default=0)

        # Phase 1: паркуем неверные units на временные позиции (>> max)
        temp_positions: dict[int, int] = {}
        for i, uid in enumerate(misplaced):
            temp_pos = max_pos + 100 + i
            try:
                self.client.update_unit(
                    uid,
                    {"section": section_id, "lesson": lesson_by_unit[uid], "position": temp_pos},
                )
                temp_positions[uid] = temp_pos
                print(f"      unit {uid}: parked at {temp_pos}")
            except Exception as exc:
                print(f"      unit {uid}: failed to park: {exc}")

        # Phase 2: ставим каждый unit на целевую позицию (от меньшей к большей)
        for uid, (_, target_pos) in sorted(misplaced.items(), key=lambda kv: kv[1][1]):
            if uid not in temp_positions:
                continue
            try:
                self.client.update_unit(
                    uid,
                    {"section": section_id, "lesson": lesson_by_unit[uid], "position": target_pos},
                )
                print(f"      unit {uid}: moved → {target_pos}")
            except Exception as exc:
                print(f"      unit {uid}: failed to move to {target_pos}: {exc}")

        # Обновляем локальные unit_info.position, чтобы structure.json отражал новый порядок
        for entry in managed:
            if entry["unit_id"] in target:
                entry.setdefault("unit_info", {})["position"] = entry["position"]
        self._save_course_data()

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
