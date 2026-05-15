"""Сценарий скачивания материалов курса из Stepik."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from .lesson_manifest import load_manifest, save_manifest, upsert_step
from .step_storage import save_step
from .step_types import SUPPORTED_STEP_TYPES

if TYPE_CHECKING:
    from ..config import EditorConfig
    from .api import StepikAPIClient


class DownloadWorkflowMixin:
    if TYPE_CHECKING:
        structure: list[dict[str, Any]]
        root_folder: Path
        total_lessons: int
        config: EditorConfig
        client: StepikAPIClient

        def get_lesson_steps(self, lesson_id: int) -> list[dict[str, Any]]: ...
        def download_images(
            self,
            html: str,
            lesson_folder: Path | str,
            images_folder: str = ...,
            step_num: int | None = ...,
        ) -> str: ...
        def save_step_html(self, step_html: str, filepath: Path | str) -> None: ...

    def download_course(
        self,
        module_num: int | None = None,
        lesson_num: int | None = None,
        step_num: int | None = None,
    ) -> None:
        """Скачивает курс целиком или только выбранную часть."""
        if module_num is not None:
            sections_to_process = [(module_num, self.structure[module_num - 1])]
        else:
            sections_to_process = list(enumerate(self.structure, 1))

        lesson_counter = 0
        section_folder: Path | None = None
        lesson_folder: Path | None = None

        for section_num, section in sections_to_process:
            section_title = section["section_title"]
            lessons_list = section["lessons"]

            if lesson_num is not None:
                lessons_to_process = [(lesson_num, lessons_list[lesson_num - 1])]
            else:
                lessons_to_process = list(enumerate(lessons_list, 1))

            print(f"\n  Module {section_num}: {section_title}")
            if module_num is not None and lesson_num is None:
                print(f"     Lessons: {len(lessons_list)}\n")

            section_folder = self._create_section_folder(section_num)

            for current_lesson_num, lesson_info in lessons_to_process:
                lesson_counter += 1
                lesson_id = lesson_info["lesson_id"]
                lesson_title = lesson_info["lesson_title"]

                if lesson_num is None and module_num is None:
                    total = self.total_lessons
                elif lesson_num is None:
                    total = len(lessons_list)
                else:
                    total = 1

                if step_num is None:
                    print(
                        f"  [{lesson_counter}/{total}] "
                        f"Lesson {current_lesson_num}: {lesson_title}"
                    )
                else:
                    print(f"    Lesson {current_lesson_num}: {lesson_title}")

                lesson_folder = self._create_lesson_folder(
                    section_folder=section_folder,
                    lesson_num=current_lesson_num,
                )
                lesson_steps = self.get_lesson_steps(lesson_id)

                if not lesson_steps:
                    print("    WARNING: no supported steps found")
                    continue

                if step_num is not None:
                    lesson_steps = [
                        s for s in lesson_steps if s.get("position") == step_num
                    ]

                if lesson_steps:
                    self._process_lesson_steps(
                        lesson_id=lesson_id,
                        lesson_steps=lesson_steps,
                        lesson_folder=lesson_folder,
                        full_sync=step_num is None,
                    )
                else:
                    print(
                        f"    WARNING: step {step_num} not found "
                        "or its type is not supported"
                    )

        self._print_completion_message(
            module_num=module_num,
            lesson_num=lesson_num,
            step_num=step_num,
            section_folder=section_folder,
            lesson_folder=lesson_folder,
        )

    def _create_section_folder(self, section_num: int) -> Path:
        section_folder = self.root_folder / f"{section_num:02d}"
        section_folder.mkdir(parents=True, exist_ok=True)
        return section_folder

    def _create_lesson_folder(self, section_folder: Path, lesson_num: int) -> Path:
        lesson_folder = section_folder / f"{lesson_num:02d}"
        lesson_folder.mkdir(parents=True, exist_ok=True)
        return lesson_folder

    def _process_lesson_steps(
        self,
        lesson_id: int,
        lesson_steps: list[dict[str, Any]],
        lesson_folder: Path,
        full_sync: bool = False,
    ) -> None:
        """Сохраняет шаги урока, обновляет lesson.json."""
        manifest = load_manifest(lesson_folder)
        manifest["lesson_id"] = lesson_id

        if full_sync:
            existing_positions = {s.get("position") for s in lesson_steps}
            self._cleanup_stale_steps(lesson_folder, manifest, existing_positions)
            manifest["steps"] = []

        for step in sorted(lesson_steps, key=lambda s: s.get("position", 0)):
            block = step.get("block", {})
            step_type = block.get("name")
            position = step.get("position", 0)

            if step_type not in SUPPORTED_STEP_TYPES:
                print(f"    SKIP step {position}: unsupported type {step_type!r}")
                continue

            try:
                image_downloader = (
                    self.download_images if self.config.download_images else None
                )
                step_entry = save_step(
                    step_source=step,
                    lesson_folder=lesson_folder,
                    api_client=self.client,
                    image_downloader=image_downloader,
                )
                upsert_step(manifest, step_entry)
                print(f"    OK step {position} [{step_type}]")
            except Exception as exc:
                print(f"    ERROR step {position} [{step_type}]: {exc}")

        save_manifest(lesson_folder, manifest)

    def _cleanup_stale_steps(
        self,
        lesson_folder: Path,
        manifest: dict[str, Any],
        current_positions: set[int],
    ) -> None:
        """Удаляет подпапки шагов, которых больше нет на Stepik."""
        from .step_storage import delete_step_folder

        for step in manifest.get("steps", []):
            pos = step["position"]
            if pos in current_positions:
                continue
            step_type = step.get("type", "")
            delete_step_folder(lesson_folder, pos, step_type)
            print(f"    REMOVED stale step {pos} [{step_type}]")

    def _print_completion_message(
        self,
        module_num: int | None,
        lesson_num: int | None,
        step_num: int | None,
        section_folder: Path | None,
        lesson_folder: Path | None,
    ) -> None:
        if step_num is not None:
            print(f"\nDone. Step saved to: {lesson_folder}")
        elif lesson_num is not None:
            print(f"\nDone. Lesson saved to: {lesson_folder}")
        elif module_num is not None:
            print(f"\nDone. Module saved to: {section_folder}")
        else:
            print(f"\nDone. Course saved to: {self.root_folder}")
