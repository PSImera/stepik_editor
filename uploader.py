import json
from pathlib import Path

from src.config import EditorConfig
from src.stepik_downloader import CourseDownloader

if __name__ == "__main__":
    defaults = json.loads(Path("course_config.json").read_text(encoding="utf-8"))
    all_courses: dict[str, int] = defaults["courses"]
    active: list[str] = defaults.get("upload", [])
    courses = {name: all_courses[name] for name in active if name in all_courses}

    for course_name, course_id in courses.items():
        print(f"\n=== курс {course_name} ({course_id}) ===")
        config = EditorConfig(course_id=course_id, course_name=course_name)
        uploader = CourseDownloader(config)

        # Шаг 1: синхронизирует структуру — создаёт новые уроки (lesson_id=0),
        # записывает реальные lesson_id в structure.json,
        # удаляет осиротевшие юниты (уроки, убранные из модуля локально).
        uploader.upload_structure(sync_deletions=True)

        # Шаг 2: загружаем шаги нужных модулей
        uploader.upload_course(module_num=4)
        uploader.upload_course(module_num=5)

        # Для точечной загрузки раскомментируй нужное:
        # uploader.upload_course(module_num=4, lesson_num=3)
        # uploader.upload_course(module_num=5, lesson_num=6)
        # uploader.upload_course(module_num=5, lesson_num=6, step_num=1)