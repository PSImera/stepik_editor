"""Константы поддерживаемых типов Stepik step-source."""

# Шаги с только HTML-контентом
TEXT_STEP_TYPES: set[str] = {"text"}

# Шаги с HTML + параметрами (возможно рецензирование)
FREE_ANSWER_STEP_TYPES: set[str] = {"free-answer"}

# Задачи на программирование с checker-кодом
CODE_STEP_TYPES: set[str] = {"code"}

# Задачи с данными (generate/solve/check в Python)
DATASET_STEP_TYPES: set[str] = {"dataset"}

# SQL-задачи
SQL_STEP_TYPES: set[str] = {"sql"}

# HTML/CSS-задачи
HTML_TASK_STEP_TYPES: set[str] = {"html"}

# Тестовые задачи — хранятся как step.json
TEST_TASK_STEP_TYPES: set[str] = {
    "choice",
    "matching",
    "sorting",
    "fill-blanks",
    "number",
    "string",
    "random-tasks",
    "math",
    "table",
}

SUPPORTED_STEP_TYPES: set[str] = (
    TEXT_STEP_TYPES
    | FREE_ANSWER_STEP_TYPES
    | CODE_STEP_TYPES
    | DATASET_STEP_TYPES
    | SQL_STEP_TYPES
    | HTML_TASK_STEP_TYPES
    | TEST_TASK_STEP_TYPES
)

COMPLEX_STEP_TYPES: set[str] = (
    FREE_ANSWER_STEP_TYPES | CODE_STEP_TYPES | DATASET_STEP_TYPES
    | SQL_STEP_TYPES | HTML_TASK_STEP_TYPES
)
HTML_STEP_TYPES: set[str] = TEXT_STEP_TYPES | FREE_ANSWER_STEP_TYPES

MAX_LESSON_STEPS = 16
