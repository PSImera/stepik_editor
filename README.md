# Stepik Editor

> **Внимание:** это личный рабочий инструмент, не релизный продукт. API может меняться без предупреждения, обратная совместимость не гарантируется.

Инструмент для скачивания, редактирования и загрузки учебных материалов курсов на Stepik. Работает совместно с Claude Code — AI-агент читает `CLAUDE.md` и набор скилов, чтобы создавать и редактировать шаги уроков в нужном формате.

## Требования

- Python 3.10+
- Node.js (для рендеринга Mermaid-диаграмм)

## Установка

### 1. Клонировать репозиторий

```powershell
git clone --recurse-submodules <repo-url>
```

Флаг `--recurse-submodules` автоматически скачивает сторонние скилы (например, `humanizer-ru`).  
Если уже клонировали без флага — выполните отдельно:

```powershell
git submodule update --init
```

### 2. Создать виртуальное окружение

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Установить Mermaid CLI (для схем)

```powershell
npx -p @mermaid-js/mermaid-cli mmdc -h
```

### 3. Создать файл `.env`

Скопируйте и заполните:

```
CLIENT_ID=your_stepik_client_id
CLIENT_SECRET=your_stepik_client_secret
STEPIK_SESSION=your_session_cookie
```

Токены `CLIENT_ID` и `CLIENT_SECRET` берутся из [настроек API](https://stepik.org/oauth2/applications/) на Stepik — создайте приложение с типом «Client credentials».  
`STEPIK_SESSION` — значение cookie `sessionid`: откройте [stepik.org](https://stepik.org), DevTools → Application → Cookies → `sessionid`.

### 4. Настроить конфигурацию курсов

Скопируйте пример и заполните:

```powershell
copy defaults.example.json docs\defaults.json
```

Отредактируйте `docs/defaults.json`:

```json
{
  "default_course": "stepik_docs",
  "courses": {
    "stepik_docs": 4087
  },
  "download": ["stepik_docs"],
  "upload": []
}
```

| Поле | Описание |
|---|---|
| `default_course` | Курс, с которым работает Claude Code по умолчанию |
| `courses` | Справочник всех курсов: `"имя": stepik_id` |
| `download` | Список курсов для скачивания (`downloader.py`) |
| `upload` | Список курсов для загрузки (`uploader.py`) |

## Использование

### Скачать курс

Редактирует `"download"` в `docs/defaults.json`, затем:

```powershell
.venv\Scripts\python.exe downloader.py
```

Раскомментируйте `module_num`, `lesson_num`, `step_num` в `downloader.py`, чтобы точечно указать что скачивать: конкретный модуль, урок или отдельный шаг.

### Загрузить курс на Stepik

Редактирует `"upload"` в `docs/defaults.json`, затем:

```powershell
.venv\Scripts\python.exe uploader.py
```

Раскомментируйте `module_num`, `lesson_num`, `step_num` в `uploader.py`, чтобы точечно указать что загружать: конкретный модуль, урок или отдельный шаг.

### Обновить RAG-индекс

```powershell
.venv\Scripts\python.exe update_rag.py
```

Курс берётся из `default_course` в `docs/defaults.json`.

### CLI: скачивание / загрузка

```powershell
# Скачать курс
.venv\Scripts\python.exe -m src.stepik_downloader --course <course>

# Загрузить курс
.venv\Scripts\python.exe -m src.stepik_downloader --course <course> --upload
```

### CLI: RAG-индекс

```powershell
# Построить / обновить индекс
.venv\Scripts\python.exe -m src.course_rag build --course <course>

# Обновить один шаг
.venv\Scripts\python.exe -m src.course_rag update --course <course> --file courses/<course>/03/05/01_text/task.html

# Поиск
.venv\Scripts\python.exe -m src.course_rag search --course <course> --query "контекстное окно" --k 5

# Поиск только по пройденному материалу (до урока 5 модуля 3)
.venv\Scripts\python.exe -m src.course_rag search-history --course <course> --query "промпт" --module-to 3 --lesson-to 5
```

### Сгенерировать summary-файлы

Summary можно создавать двумя способами:

**Скриптом** — автоматически по всему курсу на основе TF-IDF:

```powershell
.venv\Scripts\python.exe -m src.utils.generate_lesson_summaries --course <course>
```

**Агентом (Claude Code + скил `summary`)** — вручную после завершения урока. Агент читает содержимое шагов и составляет осмысленное summary с учётом контекста курса. Используется командой `/summary` во время работы над уроком.

Оба способа создают файлы `XX-YY_summary.md` в папке урока.

### Извлечь структуру курса

```powershell
.venv\Scripts\python.exe -m src.utils.extract_course_structure --input .cache/stepik/course_<id>/structure.json
```

## Структура проекта

```
stepik_editor/
├── courses/              # Учебные материалы
│   └── <course>/
│       └── <module>/     # Нумерация с нулями: 01, 02, ...
│           └── <lesson>/
│               ├── lesson.json         # Манифест шагов (авторитетный список)
│               └── <pos>_<type>/       # Папка шага: 01_text, 03_choice, ...
│                   ├── task.html       # Контент (text, code, free-answer)
│                   └── step.json       # Тестовые задачи (choice, matching, ...)
├── docs/
│   ├── defaults.json     # Конфигурация курсов (не в git)
│   └── <course>.md       # Правила для конкретного курса
├── src/
│   ├── config.py         # EditorConfig
│   ├── stepik_downloader/ # Скачивание и загрузка
│   ├── course_rag/        # Векторный RAG-индекс
│   └── utils/             # Вспомогательные скрипты
├── .claude/
│   └── skills/            # Скилы для Claude Code
├── defaults.example.json  # Шаблон конфига
├── downloader.py
├── uploader.py
└── update_rag.py
```

## Скилы Claude Code

Скилы подключаются автоматически при работе с материалами курсов через Claude Code. Вызываются командой `/skill-name`.

| Скил | Назначение |
|---|---|
| `lesson` | Редактирование шагов урока: текстовые шаги, структура `lesson.json` |
| `test-tasks` | Генерация тестовых задач (choice, matching, fill-blanks и др.) |
| `task-programming` | Создание задач на программирование с автопроверкой |
| `task-rewiew` | Создание заданий с ревью человеком |
| `code-examples` | Валидация и оформление кодовых примеров |
| `summary` | Сохранение и чтение саммари уроков и модулей |
| `rag` | Семантический поиск по индексу курса |
| `shemas` | Генерация схем и диаграмм (Mermaid / SVG) |
| `context-links` | Перекрёстные ссылки между курсами (каталог — `docs/links-catalog.md`) |
| `public-materials` | Правила для публичного контента |
| `humanizer-ru` | Очеловечивание AI-сгенерированного текста на русском — by [Vladimir-Human](https://github.com/Vladimir-Human/humanizer-ru) |

## Каталог перекрёстных ссылок (links-catalog.md)

`docs/links-catalog.md` — реестр курсов и учёт использованных упоминаний. Скил `context-links` читает его при добавлении ссылок между курсами.

**Target Catalog** — метаданные каждого курса:

```markdown
### `my_course`

- `kind`: `local_course`          # local_course | external_course
- `local_folder`: `courses/my_course`
- `stepik_id`: `000000`
- `title`: `Название курса`
- `status`: `in_progress`         # in_progress | finished
- `promo_page`: `https://stepik.org/course/000000/promo`
- `redirect_link`: `https://example.github.io/my_course/`
- `redirect_link_25`: `https://example.github.io/my_course-discount-25/`
- `referral_link`: `https://stepik.org/a/000000?utm_source=hs`
- `discount_link_25`: `https://stepik.org/a/000000/pay?promo=PROMO_CODE`
```

**Local Course Link Ledger** — сколько упоминаний уже использовано (максимум 2 на пару курсов):

```markdown
### Source: `my_course`

- `local_folder`: `courses/my_course`
- `status`: `in_progress`
- `outbound_link_steps`:
  - `my_course`: `SELF_FORBIDDEN`
  - `other_course`: `[]`              # ещё не использовано
  - `another_course`: `["02-03-05"]`  # использовано один раз (модуль-урок-шаг)
- `violations`: `none`
```

Индекс шага в ledger — формат `MM-LL-SS` (модуль-урок-шаг).

## Курсо-специфичные правила

Файл `docs/<course>.md` содержит правила, которые Claude Code применяет только для этого курса: тематику, требования к стилю, структуру уроков, ссылку на кэш Stepik-структуры.

Пример: `docs/my_course.md` описывает тематику, стиль подачи, структуру уроков и ссылку на кэш Stepik-структуры для конкретного курса.

## Переменные конфигурации EditorConfig

Основные параметры в `src/config.py`:

| Параметр | По умолчанию | Описание |
|---|---|---|
| `course_id` | `0` | ID курса на Stepik |
| `course_name` | `my_course` | Имя папки в `courses/` |
| `download_images` | `True` | Скачивать изображения |
| `html_head` | `False` | Включать `<head>` в task.html |
| `rag_embedding_model` | `intfloat/multilingual-e5-large` | Модель эмбеддингов |
| `rag_embedding_offline` | `True` | Использовать локально кэшированную модель |
