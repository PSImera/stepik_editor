"""Фасад для сценариев скачивания и загрузки курсов Stepik."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import warnings

try:
    from src.config import EditorConfig
except ImportError:  # pragma: no cover - fallback для прямого запуска из папки src
    from config import EditorConfig

from .api import StepikAPIClient
from .course_structure import CourseStructureMixin
from .download_workflow import DownloadWorkflowMixin
from .local_steps import LocalStepsMixin
from .step_types import (
    COMPLEX_STEP_TYPES,
    HTML_STEP_TYPES,
    MAX_LESSON_STEPS,
    TEST_TASK_STEP_TYPES,
    SUPPORTED_STEP_TYPES,
    TEXT_STEP_TYPES,
)
from .structure_upload_workflow import StructureUploadMixin
from .upload_workflow import UploadWorkflowMixin

warnings.filterwarnings("ignore")


class CourseDownloader(
    CourseStructureMixin,
    DownloadWorkflowMixin,
    UploadWorkflowMixin,
    StructureUploadMixin,
    LocalStepsMixin,
):
    """Скачивает и загружает материалы курса Stepik."""

    TEXT_STEP_TYPES = TEXT_STEP_TYPES
    COMPLEX_STEP_TYPES = COMPLEX_STEP_TYPES
    TEST_TASK_STEP_TYPES = TEST_TASK_STEP_TYPES
    HTML_STEP_TYPES = HTML_STEP_TYPES
    SUPPORTED_STEP_TYPES = SUPPORTED_STEP_TYPES
    MAX_LESSON_STEPS = MAX_LESSON_STEPS

    def __init__(
        self,
        config: EditorConfig | None = None,
        api_client: StepikAPIClient | None = None,
    ):
        self.config = config or EditorConfig()
        self.client = api_client or StepikAPIClient.from_env()
        self.headers = self.client.headers
        self._get_course_info()

    def _get_store_path(self) -> Path:
        course_name = getattr(self, "course_name", None) or self.config.course_name
        return Path(self.config.course_save_folder) / course_name / "structure.json"

    def _resolve_course_id(self, course_id: int | None = None) -> int:
        if course_id is not None:
            return course_id

        if hasattr(self, "course_id") and self.course_id is not None:
            return self.course_id

        return self.config.course_id

    def _load_course_data(self) -> bool:
        store_path = self._get_store_path()
        if not store_path.exists():
            return False

        try:
            data = json.loads(store_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"⚠️ Не удалось прочитать structure.json: {exc}")
            return False

        if data.get("course_id") != self.course_id:
            return False

        self.course_info = data.get("course_info", {})
        self.course_name = data.get("course_name") or self.config.course_name
        self.structure = data.get("structure", [])
        return bool(self.structure)

    def _save_course_data(self) -> None:
        store_path = self._get_store_path()
        store_path.parent.mkdir(parents=True, exist_ok=True)
        store_path.write_text(
            json.dumps(
                {
                    "course_id": self.course_id,
                    "course_name": self.course_name,
                    "course_info": self.course_info,
                    "structure": self.structure,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def refresh_structure(self) -> None:
        """Обновляет section_id/unit_id/section_info/lesson_info из Stepik,
        сохраняя course_info и черновые уроки (lesson_id=0) из локального файла.
        """
        store_path = self._get_store_path()
        local_course_info: dict = {}
        local_structure: list = []
        if store_path.exists():
            try:
                stored = json.loads(store_path.read_text(encoding="utf-8"))
                local_course_info = stored.get("course_info", {})
                local_structure = stored.get("structure", [])
            except (OSError, json.JSONDecodeError):
                pass

        print(f"Обновление структуры курса {self.course_id} с Stepik...")
        stepik_structure = self.get_course_structure()

        self.structure = self._merge_structures(local_structure, stepik_structure)

        if local_course_info:
            self.course_info = local_course_info

        self._save_course_data()
        total = sum(len(s["lessons"]) for s in self.structure)
        print(f"Готово. Модулей: {len(self.structure)}, уроков: {total}")

    @staticmethod
    def _merge_structures(
        local: list[dict],
        stepik: list[dict],
    ) -> list[dict]:
        """Объединяет локальную структуру со свежей с Stepik.

        Правила:
        - Локальные секции обогащаются section_id/section_info по совпадению позиции.
        - Локальные уроки с lesson_id > 0 обогащаются unit_id/unit_info/lesson_info.
        - Локальные уроки с lesson_id = 0 (черновики) остаются нетронутыми.
        - Уроки/секции, которые есть на Stepik но отсутствуют локально, добавляются.
        """
        stepik_by_pos: dict[int, dict] = {
            s["section_position"]: s for s in stepik
        }
        local_by_pos: dict[int, dict] = {
            s["section_position"]: s for s in local
        }

        merged_sections: list[dict] = []

        all_positions = sorted(set(stepik_by_pos) | set(local_by_pos))
        for pos in all_positions:
            local_sec = local_by_pos.get(pos)
            stepik_sec = stepik_by_pos.get(pos)

            if local_sec is None:
                # секция есть на Stepik, но не локально — добавляем
                if stepik_sec is not None:
                    merged_sections.append(stepik_sec)
                continue

            if stepik_sec is None:
                # секция только локальная (ещё не создана на Stepik) — оставляем
                merged_sections.append(local_sec)
                continue

            # секция есть с обеих сторон — обогащаем локальную данными с Stepik
            merged_sec = {
                **local_sec,
                "section_id": stepik_sec["section_id"],
                "section_info": stepik_sec["section_info"],
            }
            merged_sec["lessons"] = CourseDownloader._merge_lessons(
                local_sec.get("lessons", []),
                stepik_sec.get("lessons", []),
            )
            merged_sections.append(merged_sec)

        return merged_sections

    @staticmethod
    def _merge_lessons(local: list[dict], stepik: list[dict]) -> list[dict]:
        stepik_by_lesson_id: dict[int, dict] = {
            l["lesson_id"]: l for l in stepik if l["lesson_id"]
        }
        stepik_by_pos: dict[int, dict] = {l["position"]: l for l in stepik}
        local_lesson_ids = {l["lesson_id"] for l in local if l["lesson_id"]}

        merged: list[dict] = []
        for lesson in local:
            lesson_id = lesson.get("lesson_id") or 0
            if lesson_id == 0:
                # черновик — оставляем как есть
                merged.append(lesson)
                continue
            stepik_lesson = stepik_by_lesson_id.get(lesson_id)
            if stepik_lesson:
                merged.append({
                    **lesson,
                    "unit_id": stepik_lesson["unit_id"],
                    "unit_info": stepik_lesson["unit_info"],
                    "lesson_info": stepik_lesson["lesson_info"],
                })
            else:
                merged.append(lesson)

        # уроки, которые есть на Stepik но не локально — добавляем
        for stepik_lesson in stepik:
            if stepik_lesson["lesson_id"] not in local_lesson_ids:
                merged.append(stepik_lesson)

        merged.sort(key=lambda l: l["position"])
        return merged

    def delete_store(self, course_id: int | None = None) -> None:
        store_path = self._get_store_path()
        if store_path.exists():
            store_path.unlink()
            print(f"structure.json удалён: {store_path}")
        else:
            print(f"structure.json не найден: {store_path}")

    def clear_cash(self, course_id: int | None = None) -> None:
        """Устаревший метод — используй delete_store()."""
        self.delete_store(course_id=course_id)

    def clear_cache(self, course_id: int | None = None) -> None:
        """Устаревший метод — используй delete_store()."""
        self.delete_store(course_id=course_id)
