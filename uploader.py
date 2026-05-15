import json
from pathlib import Path

from src.config import EditorConfig
from src.stepik_downloader import CourseDownloader

if __name__ == "__main__":
    defaults = json.loads(Path("docs/defaults.json").read_text(encoding="utf-8"))
    all_courses: dict[str, int] = defaults["courses"]
    active: list[str] = defaults.get("upload", [])
    courses = {name: all_courses[name] for name in active if name in all_courses}

    for course_name, course_id in courses.items():
        print(f"\n=== курс {course_name} ({course_id}) ===")
        config = EditorConfig(course_id=course_id, course_name=course_name)
        uploader = CourseDownloader(config)

        uploader.upload_course(
            # module_num=1,
            # lesson_num=1,
            # step_num=1,
        )
