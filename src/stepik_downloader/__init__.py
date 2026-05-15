"""Пакет для загрузки структуры и материалов курса из Stepik.

Модуль экспортирует основной orchestration-класс `CourseDownloader`.
Остальные подмодули разделяют ответственность между API-клиентом,
форматированием HTML/markdown и хранением файлов тестовых вопросов.
Карта модулей и правила расширения описаны в `README.md` рядом с кодом.
"""

from .course_downloader import CourseDownloader

__all__ = ["CourseDownloader"]
