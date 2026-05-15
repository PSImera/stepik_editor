# stepik_downloader: заметки для разработчиков

Пакет отвечает за синхронизацию материалов Stepik с локальной структурой курса.
Основная точка входа для кода снаружи пакета: `CourseDownloader` из
`src.stepik_downloader`.

`CourseDownloader` является фасадом: он собирает в один класс несколько
смысловых mixin-модулей. Каждый mixin отвечает за отдельную область: структуру
курса, скачивание, загрузку или работу с локальными файлами. Такая организация
помогает добавлять новые типы шагов и новые операции в конкретном модуле, а не
разбирать один большой orchestration-файл.

## Карта модулей

- `course_downloader.py` - фасад `CourseDownloader`, общая инициализация и
  кеш структуры курса.
- `api.py` - низкоуровневый HTTP-клиент Stepik API: авторизация, чтение
  сущностей, пагинация, создание/обновление/удаление `step-source`.
- `course_structure.py` - загрузка метаданных курса, секций, уроков и шагов.
- `download_workflow.py` - сценарий скачивания: обход модулей и уроков,
  сохранение шагов в локальные файлы.
- `upload_workflow.py` - сценарий загрузки локальных материалов на Stepik:
  построение локального плана урока, создание/перезапись шагов, удаление
  лишних поддерживаемых шагов.
- `lesson_manifest.py` - единственный источник истины о шагах урока:
  чтение/запись `lesson.json`, вычисление пути подпапки шага (`step_folder`),
  `load_manifest` / `save_manifest` / `upsert_step` / `get_step_entry`.
- `step_storage.py` - сериализация шагов: Stepik API ↔ локальные файлы.
  `save_step()` сохраняет шаг из API в подпапку и возвращает запись для
  `lesson.json`; `load_step()` читает локальные файлы и собирает `block` для
  загрузки обратно на платформу. Охватывает все поддерживаемые типы, включая
  `text`, `free-answer`, `code`, `dataset`, `sql`, `html` и тестовые задачи.
- `local_steps.py` - работа с локальными HTML-файлами шагов, картинками и
  относительными ссылками.
- `step_types.py` - единое место с константами поддерживаемых типов шагов.
- `html_utils.py` - небольшие функции для очистки HTML и получения текста.
- `cli.py` и `__main__.py` - минимальные точки запуска из командной строки.

## Основные потоки данных

### Скачивание

1. `CourseDownloader.download_course()` из `download_workflow.py` выбирает
   нужные модуль, урок и шаг.
2. `get_lesson_steps()` из `course_structure.py` получает `step-sources` и
   оставляет только типы из `SUPPORTED_STEP_TYPES`.
3. Каждый шаг сохраняется через `step_storage.save_step()`, которая создаёт
   подпапку `{pos:02d}_{type}/` и записывает нужные файлы.
4. Метаданные шага (`step_source_id`, `type`, `cost` и доп. поля) добавляются
   в `lesson.json` через `lesson_manifest.upsert_step()` /
   `lesson_manifest.save_manifest()`.

### Загрузка

1. `CourseDownloader.upload_course()` из `upload_workflow.py` читает `lesson.json`
   через `lesson_manifest.load_manifest()`.
2. Для каждого шага из манифеста `step_storage.load_step()` читает локальные
   файлы и собирает Stepik `block`.
3. `_write_lesson_steps_by_position()` создаёт или перезаписывает шаги на
   платформе.
4. При загрузке урока целиком `_delete_extra_lesson_steps()` удаляет лишние
   поддерживаемые шаги вне локального плана.

## Как добавлять новый тип тестовой задачи

Тестовые задачи хранятся как `step.json` в подпапке `{pos:02d}_{type}/`.

Минимальный чеклист:

1. Добавить имя типа в `TEST_TASK_STEP_TYPES` в `step_types.py`.
2. В `step_storage._save_question()` добавить ветку `elif step_type == "..."`,
   которая записывает нужные поля из `source` в словарь `data`.
3. В `step_storage._load_question()` добавить зеркальную ветку, которая
   собирает `source` обратно из `data` для загрузки на Stepik.
4. Проверить загрузку в режиме `dry_run=True`, если тип участвует в upload.

Важно: при обновлении существующего Stepik-шага функции должны по возможности
сохранять неизвестные поля `source`. Элементы из существующего `source`
копируются, затем обновляются только поля, которые задаются локальным
`step.json`.

## Как добавлять новый HTML-подобный тип шага

Если новый тип хранит основной контент в `block["text"]` и может сохраняться как
HTML, обычно достаточно:

1. Добавить тип в `HTML_STEP_TYPES` в `step_types.py`.
2. Проверить, что `_process_step()` корректно читает нужное поле.
3. Проверить, что `_build_text_step_block()` подходит для обратной загрузки.

Если структура `block` отличается от обычного `text`, лучше не расширять
`_process_step()` большим условием, а вынести отдельный обработчик рядом с
`question_types.py` или добавить отдельный модуль для таких шагов.

## Публичные точки

- Основной импорт: `from src.stepik_downloader import CourseDownloader`.
- Основные операции: `download_course()` и `upload_course()`.
- Вспомогательные методы, которые могут использовать скрипты вокруг пакета:
  `sanitize_filename()`, `extract_step_name()`, `get_theory()`, `clear_cache()`
  и `clear_cash()`.
- Для работы с манифестом урока вне пакета используйте функции из
  `lesson_manifest`: `load_manifest()`, `save_manifest()`, `upsert_step()`,
  `get_step_entry()`, `step_folder()`.
- Для прямой сериализации шагов используйте `step_storage.save_step()` и
  `step_storage.load_step()`.

## Проверки после изменений

Быстрая проверка синтаксиса:

```powershell
.\.venv\Scripts\python.exe -m compileall -q src\stepik_downloader
```

Проверка базовых импортов:

```powershell
.\.venv\Scripts\python.exe -c "from src.stepik_downloader import CourseDownloader; print(CourseDownloader.__name__)"
```

Для изменений в загрузке на платформу сначала используйте `dry_run=True`, чтобы
увидеть план без записи в Stepik.
