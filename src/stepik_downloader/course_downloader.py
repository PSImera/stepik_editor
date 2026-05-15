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
from .upload_workflow import UploadWorkflowMixin

warnings.filterwarnings("ignore")


class CourseDownloader(
    CourseStructureMixin,
    DownloadWorkflowMixin,
    UploadWorkflowMixin,
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

    def _get_cache_path(self) -> Path:
        course_name = getattr(self, "course_name", None) or self.config.course_name
        return Path(self.config.course_save_folder) / course_name / "structure.json"

    def _resolve_course_id(self, course_id: int | None = None) -> int:
        if course_id is not None:
            return course_id

        if hasattr(self, "course_id") and self.course_id is not None:
            return self.course_id

        return self.config.course_id

    def _load_cached_course_data(self) -> bool:
        cache_path = self._get_cache_path()
        if not cache_path.exists():
            return False

        try:
            cached_data = json.loads(cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"⚠️ Не удалось прочитать кеш структуры курса: {exc}")
            return False

        if cached_data.get("course_id") != self.course_id:
            return False

        self.course_info = cached_data.get("course_info", {})
        cached_course_name = cached_data.get("course_name")
        self.course_name = cached_course_name or self.config.course_name
        self.structure = cached_data.get("structure", [])
        return bool(self.structure)

    def _save_cached_course_data(self) -> None:
        cache_path = self._get_cache_path()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_payload = {
            "course_id": self.course_id,
            "course_name": self.course_name,
            "course_info": self.course_info,
            "structure": self.structure,
        }
        cache_path.write_text(
            json.dumps(cache_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def clear_cash(self, course_id: int | None = None) -> None:
        """Сохраняем старое имя метода для обратной совместимости."""
        cache_path = self._get_cache_path()
        if cache_path.exists():
            cache_path.unlink()
            print(f"Кеш структуры курса удалён: {cache_path}")
        else:
            print(f"Кеш структуры курса не найден: {cache_path}")

    def clear_cache(self, course_id: int | None = None) -> None:
        self.clear_cash(course_id=course_id)
