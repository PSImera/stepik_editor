"""Загрузка структуры курса и вспомогательные методы для метаданных Stepik."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from .html_utils import sanitize_filename

if TYPE_CHECKING:
    from ..config import EditorConfig
    from .api import StepikAPIClient


class CourseStructureMixin:
    if TYPE_CHECKING:
        config: EditorConfig
        client: StepikAPIClient
        SUPPORTED_STEP_TYPES: set[str]
        HTML_STEP_TYPES: set[str]
        course_id: int
        course_info: dict[str, Any]
        structure: list[dict[str, Any]]
        course_name: str
        total_lessons: int

        def _load_course_data(self) -> bool: ...
        def _save_course_data(self) -> None: ...
    def _get_course_info(self) -> dict[str, Any] | None:
        """Загружает метаданные курса и подготавливает локальную корневую папку."""
        self.course_id = self.config.course_id
        if not self.config.course_id:
            print("❌ Не указан course_id в config.yaml")
            return None

        if not all(
            hasattr(self, attr) for attr in ("course_info", "structure", "course_name")
        ):
            if self._load_course_data():
                print(f"Структура курса {self.course_id} загружена из structure.json")
            else:
                print(f"Загрузка структуры курса {self.course_id}...")
                self.course_info = self.client.get_course(self.course_id)
                if not self.config.course_name:
                    self.course_name = sanitize_filename(
                        self.course_info.get("title", f"course_{self.course_id}")
                    )
                else:
                    self.course_name = self.config.course_name

                self.structure = self.get_course_structure()
                if self.structure:
                    self._save_course_data()

            if not self.structure:
                print("❌ Не удалось получить структуру курса.")
                return None
        else:
            print("Структура курса:")

        self.total_lessons = sum(len(section["lessons"]) for section in self.structure)
        print(f"Название курса: {self.course_name}")
        print(f"Модулей: {len(self.structure)}, Уроков: {self.total_lessons}")

        self.root_folder = Path(self.config.course_save_folder) / self.course_name
        self.root_folder.mkdir(parents=True, exist_ok=True)
        return self.course_info

    def sanitize_filename(self, name: str) -> str:
        """Сохраняем публичный метод для обратной совместимости."""
        return sanitize_filename(name)

    def get_course_structure(self) -> list[dict[str, Any]]:
        """Строит локальное представление структуры курса из sections/units/lessons."""
        structure: list[dict[str, Any]] = []
        section_ids = self.get_sections_from_course()

        if not section_ids:
            print("⚠️ Пробуем альтернативный способ получения секций...")
            section_ids = [
                section["id"] for section in self.client.list_sections(self.course_id)
            ]

        if not section_ids:
            print("❌ Не удалось получить секции курса")
            return []

        for section_id in section_ids:
            section_info = self.get_section_info(section_id)
            section_title = section_info.get("title", f"Модуль {section_id}")
            section_position = section_info.get("position", 0)
            unit_ids = section_info.get("units", [])

            if not unit_ids:
                print(f"  ⚠️ Секция '{section_title}' не содержит уроков")
                continue

            lessons = []
            for unit_id in unit_ids:
                unit_info = self.get_unit_info(unit_id)
                lesson_id = unit_info.get("lesson")
                if lesson_id:
                    lesson_info = self.client.get_lesson(lesson_id)
                    lessons.append(
                        {
                            "lesson_id": lesson_id,
                            "unit_id": unit_id,
                            "lesson_title": lesson_info.get("title", f"Урок {lesson_id}"),
                            "position": unit_info.get("position", 0),
                            "lesson_info": lesson_info,
                            "unit_info": unit_info,
                        }
                    )

            lessons.sort(key=lambda lesson: lesson["position"])
            if lessons:
                structure.append(
                    {
                        "section_id": section_id,
                        "section_title": section_title,
                        "section_position": section_position,
                        "section_info": section_info,
                        "lessons": lessons,
                    }
                )

        structure.sort(key=lambda section: section["section_position"])
        return structure

    def get_sections_from_course(self) -> list[int]:
        """Возвращает список id секций из метаданных курса."""
        section_ids = self.course_info.get("sections", [])
        if section_ids:
            return section_ids

        print("⚠️ Список секций в курсе пуст")
        return []

    def get_section_info(self, section_id: int) -> dict[str, Any]:
        """Публичный прокси к API клиента для секции."""
        return self.client.get_section(section_id)

    def get_unit_info(self, unit_id: int) -> dict[str, Any]:
        """Публичный прокси к API клиента для unit."""
        return self.client.get_unit(unit_id)

    def get_lesson_title(self, lesson_id: int) -> str:
        """Возвращает заголовок урока или запасное имя при ошибке API."""
        try:
            lesson = self.client.get_lesson(lesson_id)
            return lesson.get("title", f"Урок {lesson_id}")
        except Exception:
            return f"Урок {lesson_id}"

    def get_lesson_steps(self, lesson_id: int) -> list[dict[str, Any]]:
        """Возвращает только поддерживаемые шаги урока.

        Сначала пробует step-sources (инструкторский API, возвращает полные данные
        включая source для тестовых вопросов). Если список пуст — значит курс чужой,
        делает фоллбэк на публичный /api/steps (только HTML-шаги без source).
        """
        raw_steps = self.client.get_step_sources(lesson_id)
        if not raw_steps:
            raw_steps = self.client.get_steps(lesson_id)
        lesson_steps = [
            step
            for step in raw_steps
            if step.get("block", {}).get("name") in self.SUPPORTED_STEP_TYPES
        ]
        lesson_steps.sort(key=lambda step: step.get("position", 0))
        return lesson_steps

    def get_theory(self, lesson_id: int) -> list[dict[str, Any]]:
        """Возвращает только HTML-теорию урока в старом совместимом формате."""
        theory_blocks = []
        for step in self.client.get_steps(lesson_id):
            block = step.get("block", {})
            if block.get("name") in self.HTML_STEP_TYPES:
                html = block.get("text", "").strip()
                if html:
                    theory_blocks.append(
                        {"position": step.get("position", 0), "html": html}
                    )
        theory_blocks.sort(key=lambda block: block["position"])
        return theory_blocks
