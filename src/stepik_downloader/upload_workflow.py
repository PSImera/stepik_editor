"""Сценарий загрузки локальных материалов обратно в Stepik."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from .lesson_manifest import load_manifest, save_manifest, upsert_step
from .step_storage import load_step, load_step_instruction
from .step_types import MAX_LESSON_STEPS, SUPPORTED_STEP_TYPES

if TYPE_CHECKING:
    from .api import StepikAPIClient


class UploadWorkflowMixin:
    if TYPE_CHECKING:
        client: StepikAPIClient
        structure: list[dict[str, Any]]
        root_folder: Path
        SUPPORTED_STEP_TYPES: set[str]

        def upload_structure(self, *, dry_run: bool = False, sync_deletions: bool = False) -> None: ...  # noqa: ARG002

    def upload_course(
        self,
        module_num: int | None = None,
        lesson_num: int | None = None,
        step_num: int | None = None,
        *,
        dry_run: bool = False,
        steps_per_lesson: int = MAX_LESSON_STEPS,
        sync_structure: bool = False,
    ) -> None:
        """Загружает локальные материалы обратно в существующий курс Stepik.

        sync_structure=True — сначала синхронизирует описание курса, модули и уроки
        из structure.json в Stepik (создаёт/переименовывает), затем загружает шаги.
        """
        if sync_structure:
            self.upload_structure(dry_run=dry_run, sync_deletions=True)
        if module_num is not None:
            sections_to_process = [(module_num, self.structure[module_num - 1])]
        else:
            sections_to_process = list(enumerate(self.structure, 1))

        stats = {
            "uploaded": 0,
            "planned": 0,
            "missing": 0,
            "created": 0,
            "deleted": 0,
            "invalid": 0,
            "failed": 0,
        }

        for section_num, section in sections_to_process:
            section_title = section["section_title"]
            lessons_list = section["lessons"]

            if lesson_num is not None:
                lessons_to_process = [(lesson_num, lessons_list[lesson_num - 1])]
            else:
                lessons_to_process = list(enumerate(lessons_list, 1))

            print(f"\nModule {section_num}: {section_title}")

            for current_lesson_num, lesson_info in lessons_to_process:
                lesson_id = lesson_info["lesson_id"]
                lesson_title = lesson_info["lesson_title"]
                lesson_folder = (
                    self.root_folder / f"{section_num:02d}" / f"{current_lesson_num:02d}"
                )

                print(f"  Lesson {current_lesson_num}: {lesson_title}")

                lesson_folder.mkdir(parents=True, exist_ok=True)
                manifest = load_manifest(lesson_folder)
                manifest.setdefault("lesson_id", lesson_id)
                steps_in_manifest = manifest.get("steps", [])

                if not steps_in_manifest:
                    if step_num is not None:
                        print("    No steps in lesson.json")
                        stats["missing"] += 1
                        continue
                    # Полная синхронизация: оба пустые → заглушка; удалённый непустой → ошибка
                    all_lesson_steps = self.client.get_step_sources(lesson_id)
                    if all_lesson_steps:
                        print(
                            f"    ERROR: remote has {len(all_lesson_steps)} step(s) "
                            "but local is empty — skipping to avoid overwriting with nothing"
                        )
                        stats["failed"] += 1
                        continue
                    # Оба пустые — создаём заглушку
                    if dry_run:
                        print("    will create stub (both local and remote are empty)")
                        stats["planned"] += 1
                        continue
                    step_dir = lesson_folder / "01_text"
                    step_dir.mkdir(exist_ok=True)
                    (step_dir / "task.html").write_text(
                        "<p>Урок в разработке.</p>", encoding="utf-8"
                    )
                    upsert_step(manifest, {"position": 1, "type": "text", "cost": 0})
                    save_manifest(lesson_folder, manifest)
                    steps_in_manifest = manifest["steps"]
                    print("    stub created")

                if step_num is not None:
                    steps_in_manifest = [
                        s for s in steps_in_manifest if s["position"] == step_num
                    ]

                all_lesson_steps = self.client.get_step_sources(lesson_id)
                all_lesson_steps.sort(key=lambda s: s.get("position", 0))

                upload_results = self._write_lesson_steps_by_position(
                    lesson_id=lesson_id,
                    all_lesson_steps=all_lesson_steps,
                    manifest_steps=steps_in_manifest,
                    manifest=manifest,
                    lesson_folder=lesson_folder,
                    steps_per_lesson=steps_per_lesson,
                    dry_run=dry_run,
                )
                for result in upload_results:
                    stats[result] += 1

                if step_num is None:
                    local_positions = {s["position"] for s in steps_in_manifest}
                    cleanup_results = self._delete_extra_lesson_steps(
                        lesson_id=lesson_id,
                        local_step_numbers=local_positions,
                        steps_per_lesson=steps_per_lesson,
                        dry_run=dry_run,
                    )
                    for result in cleanup_results:
                        stats[result] += 1

        mode = "dry-run" if dry_run else "upload"
        print(
            f"\nDone ({mode}): "
            f"updated {stats['uploaded']}, "
            f"created {stats['created']}, "
            f"deleted {stats['deleted']}, "
            f"errors {stats['failed']}, "
            f"planned {stats['planned']}, "
            f"missing {stats['missing']}, "
            f"invalid {stats['invalid']}"
        )

    def _write_lesson_steps_by_position(
        self,
        lesson_id: int,
        all_lesson_steps: list[dict[str, Any]],
        manifest_steps: list[dict[str, Any]],
        manifest: dict[str, Any],
        lesson_folder: Path,
        *,
        steps_per_lesson: int,
        dry_run: bool,
    ) -> list[str]:
        results: list[str] = []
        remote_by_id: dict[int, dict[str, Any]] = {s["id"]: s for s in all_lesson_steps}
        remote_by_position: dict[int, dict[str, Any]] = {
            s["position"]: s for s in all_lesson_steps
        }
        # ID шагов, уже привязанных к конкретным записям манифеста — не отдавать при поиске по позиции
        claimed_ids: set[int] = {
            e["step_source_id"]
            for e in manifest_steps
            if e.get("step_source_id")
        }

        for manifest_entry in sorted(manifest_steps, key=lambda s: s["position"]):
            position = manifest_entry["position"]
            raw_type = manifest_entry.get("type", "?").replace("-", "_")
            instruction_type = manifest_entry.get("instruction_type")
            step_type = f"{raw_type}:{instruction_type}" if instruction_type else raw_type
            if position > steps_per_lesson:
                print(f"    Step {position}: exceeds limit {steps_per_lesson}")
                results.append("invalid")
                continue

            try:
                block, cost, label = load_step(
                    manifest_entry=manifest_entry,
                    lesson_folder=lesson_folder,
                )
            except Exception as exc:
                print(f"    Step {position}: parse error: {exc}")
                results.append("invalid")
                continue

            instruction = load_step_instruction(
                manifest_entry=manifest_entry,
                lesson_folder=lesson_folder,
            )

            # Ищем шаг: сначала по step_source_id, потом по позиции (только незанятые)
            manifest_ssid = manifest_entry.get("step_source_id")
            existing: dict[str, Any] | None = None
            if manifest_ssid:
                existing = remote_by_id.get(manifest_ssid)
            if existing is None:
                pos_step = remote_by_position.get(position)
                if pos_step and pos_step["id"] not in claimed_ids:
                    existing = pos_step

            if dry_run:
                action = "will update" if existing else "will create"
                print(f"    Step {position}: {action}: [{step_type}] {label}")
                results.append("planned")
                continue

            try:
                if existing:
                    step_source_id = existing["id"]
                    # Позиция и cost всегда передаются в патч — Stepik сам переставит шаг
                    self.client.update_step_source_block(
                        step_source_id=step_source_id,
                        block=block,
                        position=position,
                        cost=cost,
                    )
                    # Линкуем инструкцию если: шаг найден по позиции, или инструкция не совпадает
                    remote_instr = existing.get("instruction")
                    manifest_instr_id = manifest_entry.get("instruction_id")
                    need_link = not manifest_ssid or remote_instr != manifest_instr_id
                    if instruction:
                        self._sync_instruction(
                            step_source_id=step_source_id,
                            manifest_entry=manifest_entry,
                            instruction=instruction,
                            manifest=manifest,
                            lesson_folder=lesson_folder,
                            block=block,
                            position=position,
                            cost=cost,
                            step_is_new=need_link,
                        )
                    if not manifest_ssid:
                        upsert_step(manifest, {**manifest_entry, "step_source_id": step_source_id})
                        save_manifest(lesson_folder, manifest)
                        print(f"      step_source_id saved: {step_source_id}")
                    print(f"    Step {position}: updated: [{step_type}] {label}")
                    results.append("uploaded")
                else:
                    created = self.client.create_step_source(
                        lesson_id=lesson_id,
                        block=block,
                        position=position,
                        cost=cost,
                    )
                    step_source_id = created.get("id")
                    if not step_source_id:
                        raise RuntimeError("Stepik did not return step-source id")
                    if instruction:
                        self._sync_instruction(
                            step_source_id=step_source_id,
                            manifest_entry=manifest_entry,
                            instruction=instruction,
                            manifest=manifest,
                            lesson_folder=lesson_folder,
                            block=block,
                            position=position,
                            cost=cost,
                            step_is_new=True,
                        )
                    else:
                        # Без инструкции позиция могла не выставиться при create_step_source
                        self._ensure_step_source_position(
                            step_source_id=step_source_id,
                            target_position=position,
                            block=block,
                        )
                    upsert_step(manifest, {**manifest_entry, "step_source_id": step_source_id})
                    save_manifest(lesson_folder, manifest)
                    print(f"    Step {position}: created: [{step_type}] {label}")
                    results.append("created")
            except Exception as exc:
                print(f"    Step {position}: error: {label}")
                print(f"      {exc}")
                results.append("failed")

        return results

    def _sync_instruction(
        self,
        step_source_id: int,
        manifest_entry: dict[str, Any],
        instruction: dict[str, Any],
        manifest: dict[str, Any],
        lesson_folder: Path,
        block: dict[str, Any],
        position: int,
        cost: int,
        *,
        step_is_new: bool,
    ) -> None:
        """Создаёт или обновляет инструкцию рецензирования; сохраняет id в lesson.json."""
        instruction_id = instruction["instruction_id"]
        instruction_type = instruction["instruction_type"]
        instr_data = instruction["data"]

        if instruction_id:
            update_payload = {k: v for k, v in instr_data.items() if k != "rubrics"}
            self.client.update_instruction(instruction_id, update_payload)
            self._sync_rubrics(instruction_id, instr_data.get("rubrics", []))
            # Привязываем к шагу только если шаг новый (для старых шагов уже привязана)
            if step_is_new:
                self.client.link_instruction_to_step(
                    step_source_id, instruction_id, instruction_type, block, position, cost
                )
                print(f"      instruction linked: id={instruction_id}")
        else:
            # Проверяем, не была ли инструкция создана ранее (например, при прерванном запуске)
            existing_instr = self.client.get_instruction_for_step(step_source_id)
            instruction_id = existing_instr.get("id")
            if instruction_id:
                print(f"      instruction already exists: id={instruction_id}")
            else:
                # Создаём инструкцию без рубрик, затем рубрики с её id
                instr_payload = {k: v for k, v in instr_data.items() if k != "rubrics"}
                created = self.client.create_instruction(step_source_id, instr_payload, [])
                instruction_id = created.get("id")
                if not instruction_id:
                    raise RuntimeError("Stepik did not return instruction id")
                for rubric in instr_data.get("rubrics", []):
                    self.client.create_rubric({**rubric, "instruction": instruction_id})
                print(f"      instruction created: id={instruction_id}")
            self.client.link_instruction_to_step(
                step_source_id, instruction_id, instruction_type, block
            )
            print(f"      instruction linked: id={instruction_id}")
            upsert_step(manifest, {**manifest_entry, "instruction_id": instruction_id})
            save_manifest(lesson_folder, manifest)

    def _sync_rubrics(
        self,
        instruction_id: int,
        local_rubrics: list[dict[str, Any]],
    ) -> None:
        """Синхронизирует рубрики инструкции с локальными данными по позиции."""
        remote_instr = self.client.get_instruction(instruction_id)
        remote_by_pos: dict[int, dict[str, Any]] = {
            r["position"]: r for r in remote_instr.get("rubrics", [])
        }
        local_positions = {r["position"] for r in local_rubrics}

        for rubric in local_rubrics:
            pos = rubric["position"]
            if pos in remote_by_pos:
                self.client.update_rubric(
                    remote_by_pos[pos]["id"],
                    {**rubric, "instruction": instruction_id},
                )
            else:
                self.client.create_rubric({**rubric, "instruction": instruction_id})

        for pos, remote in remote_by_pos.items():
            if pos not in local_positions:
                self.client.delete_rubric(remote["id"])

    def _ensure_step_source_position(
        self,
        step_source_id: int,
        target_position: int,
        block: dict[str, Any],
    ) -> None:
        self.client.update_step_source_position(
            step_source_id=step_source_id,
            position=target_position,
            block=block,
        )

    def _delete_extra_lesson_steps(
        self,
        lesson_id: int,
        local_step_numbers: set[int],
        steps_per_lesson: int,
        *,
        dry_run: bool,
    ) -> list[str]:
        all_lesson_steps = self.client.get_step_sources(lesson_id)
        to_delete = [
            s for s in all_lesson_steps
            if self._should_delete_extra_step(s, local_step_numbers, steps_per_lesson)
        ]
        results: list[str] = []
        for step in sorted(to_delete, key=lambda s: s.get("position", 0), reverse=True):
            result = self._delete_stepik_step(step=step, dry_run=dry_run)
            results.append(result)
        return results

    def _should_delete_extra_step(
        self,
        step: dict[str, Any],
        local_step_numbers: set[int],
        steps_per_lesson: int,
    ) -> bool:
        position = step.get("position", 0)
        step_type = step.get("block", {}).get("name")
        if position > steps_per_lesson:
            return True
        return step_type in SUPPORTED_STEP_TYPES and position not in local_step_numbers

    def _delete_stepik_step(self, step: dict[str, Any], *, dry_run: bool) -> str:
        position = step.get("position", 0)
        step_type = step.get("block", {}).get("name")
        if dry_run:
            print(f"    Step {position}: will delete [{step_type}]")
            return "planned"
        self.client.delete_step_source(step_source_id=step["id"])
        print(f"    Step {position}: deleted [{step_type}]")
        return "deleted"
