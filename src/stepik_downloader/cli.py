"""Минимальная CLI-обёртка вокруг `CourseDownloader`.

Этот модуль сохраняет простое поведение старого скрипта:
создаёт конфиг по умолчанию и скачивает курс с глубиной,
указанной в самом вызывающем коде или в конфиге.
"""

from __future__ import annotations

import sys

try:
    from src.config import EditorConfig
except ImportError:  # pragma: no cover - fallback для прямого запуска из папки src
    from config import EditorConfig

from .course_downloader import CourseDownloader


def main() -> None:
    """Запускает скачивание курса с конфигом по умолчанию."""
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        try:
            reconfigure(encoding="utf-8")
        except Exception:
            pass

    config = EditorConfig()
    downloader = CourseDownloader(config)
    downloader.download_course()
