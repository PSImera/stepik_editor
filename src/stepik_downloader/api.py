"""HTTP-клиент для Stepik API.

Модуль инкапсулирует получение OAuth-токена, базовые запросы к REST API
и пагинацию. Это позволяет держать сетевую логику отдельно от
файловой структуры и форматирования материалов курса.
"""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
import httpx
import requests  # оставляем только для HTTPError в сигнатурах старых вызовов

load_dotenv()


class StepikAPIClient:
    """Небольшой клиент поверх Stepik API с авторизацией по client credentials."""

    def __init__(self, token: str, client: httpx.Client):
        self.token = token
        self.client = client
        self.headers = {"Authorization": f"Bearer {token}"}

    @classmethod
    def from_env(cls) -> "StepikAPIClient":
        """Создаёт клиента из переменных окружения.

        Обязательные: CLIENT_ID, CLIENT_SECRET.
        Опциональный: STEPIK_SESSION — значение cookie sessionid из браузера;
        нужен для write-операций, которые Cloudflare WAF блокирует при работе
        только через OAuth Bearer-токен.
        """
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv("CLIENT_SECRET")
        if client_id is None or client_secret is None:
            raise ValueError("CLIENT_ID и CLIENT_SECRET должны быть указаны в .env")

        http_client = httpx.Client(http2=True, follow_redirects=True, timeout=30.0)

        session_cookie = os.getenv("STEPIK_SESSION", "").strip()
        if session_cookie:
            http_client.cookies.set("sessionid", session_cookie, domain="stepik.org")

        token = cls._get_token(client_id, client_secret, http_client)
        api = cls(token=token, client=http_client)
        api._prefetch_csrf()
        return api

    @staticmethod
    def _get_token(client_id: str, client_secret: str, http_client: httpx.Client) -> str:
        """Получает access token по OAuth client credentials; сохраняет куки в клиент."""
        response = http_client.post(
            "https://stepik.org/oauth2/token/",
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )
        response.raise_for_status()
        token = response.json().get("access_token")
        if not token:
            raise RuntimeError(
                "Не удалось получить токен. Проверь client_id и client_secret."
            )
        return token

    def _prefetch_csrf(self) -> None:
        """Загружает csrftoken в клиент через GET к главной странице Stepik."""
        self.client.get("https://stepik.org/", headers=self.headers)

    def _write_headers(self) -> dict[str, str]:
        """Заголовки для изменяющих запросов: Bearer + CSRF-токен."""
        headers: dict[str, str] = {
            **self.headers,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": "https://stepik.org",
            "Referer": "https://stepik.org/",
        }
        csrf_token = self.client.cookies.get("csrftoken", "")
        if csrf_token:
            headers["X-CSRFToken"] = csrf_token
        return headers

    def get_course(self, course_id: int) -> dict[str, Any]:
        """Возвращает метаданные курса."""
        response = self.client.get(
            f"https://stepik.org/api/courses/{course_id}",
            headers=self.headers,
        )
        response.raise_for_status()
        courses = response.json().get("courses", [])
        return courses[0] if courses else {}

    def list_sections(self, course_id: int) -> list[dict[str, Any]]:
        """Возвращает список секций курса через endpoint поиска секций."""
        response = self.client.get(
            "https://stepik.org/api/sections",
            headers=self.headers,
            params={"course": course_id},
        )
        response.raise_for_status()
        return response.json().get("sections", [])

    def get_section(self, section_id: int) -> dict[str, Any]:
        """Возвращает одну секцию по id."""
        response = self.client.get(
            f"https://stepik.org/api/sections/{section_id}",
            headers=self.headers,
        )
        response.raise_for_status()
        sections = response.json().get("sections", [])
        return sections[0] if sections else {}

    def get_unit(self, unit_id: int) -> dict[str, Any]:
        """Возвращает unit по id."""
        response = self.client.get(
            f"https://stepik.org/api/units/{unit_id}",
            headers=self.headers,
        )
        response.raise_for_status()
        units = response.json().get("units", [])
        return units[0] if units else {}

    def get_lesson(self, lesson_id: int) -> dict[str, Any]:
        """Возвращает lesson по id."""
        response = self.client.get(
            f"https://stepik.org/api/lessons/{lesson_id}",
            headers=self.headers,
        )
        response.raise_for_status()
        lessons = response.json().get("lessons", [])
        return lessons[0] if lessons else {}

    def get_instruction(self, instruction_id: int) -> dict[str, Any]:
        """Возвращает инструкцию рецензирования с rubrics."""
        response = self.client.get(
            f"https://stepik.org/api/instructions/{instruction_id}",
            headers=self.headers,
        )
        response.raise_for_status()
        data = response.json()
        instructions = data.get("instructions", [])
        rubrics = data.get("rubrics", [])
        if not instructions:
            return {}
        result = dict(instructions[0])
        result["rubrics"] = rubrics
        return result

    def create_rubric(self, rubric_data: dict[str, Any]) -> dict[str, Any]:
        """Создаёт рубрику; возвращает объект с id."""
        response = self._send_json_update(
            "POST", "https://stepik.org/api/rubrics", {"rubric": rubric_data}
        )
        self._raise_for_status(response)
        data = response.json()
        rubrics = data.get("rubrics", [])
        return rubrics[0] if rubrics else {}

    def update_rubric(self, rubric_id: int, rubric_data: dict[str, Any]) -> None:
        """Обновляет рубрику."""
        url = f"https://stepik.org/api/rubrics/{rubric_id}"
        response = self._send_json_update("PUT", url, {"rubric": rubric_data})
        self._raise_for_status(response)

    def delete_rubric(self, rubric_id: int) -> None:
        """Удаляет рубрику."""
        response = self.client.delete(
            f"https://stepik.org/api/rubrics/{rubric_id}",
            headers=self._write_headers(),
        )
        if response.status_code not in (200, 204):
            self._raise_for_status(response)

    def get_instruction_for_step(self, step_source_id: int) -> dict[str, Any]:
        """Возвращает инструкцию для шага или пустой dict если не найдена."""
        response = self.client.get(
            "https://stepik.org/api/instructions",
            headers=self.headers,
            params={"step": step_source_id},
        )
        response.raise_for_status()
        data = response.json()
        instructions = data.get("instructions", [])
        return instructions[0] if instructions else {}

    def create_instruction(
        self, step_source_id: int, instruction_data: dict[str, Any], rubric_ids: list[int]
    ) -> dict[str, Any]:
        """Создаёт инструкцию рецензирования; возвращает объект с id."""
        payload = {
            **instruction_data,
            "step": step_source_id,
            "rubrics": rubric_ids,
        }
        response = self._send_json_update(
            "POST", "https://stepik.org/api/instructions", {"instruction": payload}
        )
        self._raise_for_status(response)
        data = response.json()
        instructions = data.get("instructions", [])
        return instructions[0] if instructions else {}

    def update_instruction(self, instruction_id: int, instruction_data: dict[str, Any]) -> None:
        """Обновляет существующую инструкцию рецензирования."""
        url = f"https://stepik.org/api/instructions/{instruction_id}"
        response = self._send_json_update("PUT", url, {"instruction": instruction_data})
        self._raise_for_status(response)

    def link_instruction_to_step(
        self,
        step_source_id: int,
        instruction_id: int,
        instruction_type: str,
        block: dict[str, Any],
        position: int | None = None,
        cost: int | None = None,
    ) -> None:
        """Привязывает инструкцию к step-source (top-level поля)."""
        patch: dict[str, Any] = {
            "block": block,
            "instruction": instruction_id,
            "instruction_type": instruction_type,
        }
        if position is not None:
            patch["position"] = position
        if cost is not None:
            patch["cost"] = cost
        self.update_step_source(step_source_id=step_source_id, step_source_patch=patch)

    def update_course(self, course_id: int, fields: dict[str, Any]) -> dict[str, Any]:
        """Обновляет поля описания курса."""
        response = self._send_json_update(
            "PUT", f"https://stepik.org/api/courses/{course_id}", {"course": fields}
        )
        self._raise_for_status(response)
        courses = response.json().get("courses", [])
        return courses[0] if courses else {}

    def create_section(self, course_id: int, title: str, position: int) -> dict[str, Any]:
        """Создаёт новый модуль (секцию) в курсе."""
        response = self._send_json_update(
            "POST",
            "https://stepik.org/api/sections",
            {"section": {"course": course_id, "title": title, "position": position}},
        )
        self._raise_for_status(response)
        sections = response.json().get("sections", [])
        return sections[0] if sections else {}

    def update_section(self, section_id: int, fields: dict[str, Any]) -> dict[str, Any]:
        """Обновляет поля секции (модуля)."""
        response = self._send_json_update(
            "PUT", f"https://stepik.org/api/sections/{section_id}", {"section": fields}
        )
        self._raise_for_status(response)
        sections = response.json().get("sections", [])
        return sections[0] if sections else {}

    def create_lesson(self, title: str) -> dict[str, Any]:
        """Создаёт новый урок; возвращает объект с id."""
        response = self._send_json_update(
            "POST", "https://stepik.org/api/lessons", {"lesson": {"title": title}}
        )
        self._raise_for_status(response)
        lessons = response.json().get("lessons", [])
        return lessons[0] if lessons else {}

    def update_lesson(self, lesson_id: int, title: str) -> None:
        """Переименовывает урок."""
        response = self._send_json_update(
            "PUT", f"https://stepik.org/api/lessons/{lesson_id}", {"lesson": {"title": title}}
        )
        self._raise_for_status(response)

    def create_unit(self, section_id: int, lesson_id: int, position: int) -> dict[str, Any]:
        """Создаёт unit — связь урока с секцией на заданной позиции."""
        response = self._send_json_update(
            "POST",
            "https://stepik.org/api/units",
            {"unit": {"section": section_id, "lesson": lesson_id, "position": position}},
        )
        self._raise_for_status(response)
        units = response.json().get("units", [])
        return units[0] if units else {}

    def update_unit(self, unit_id: int, fields: dict[str, Any]) -> dict[str, Any]:
        """Обновляет поля unit (например, position)."""
        response = self._send_json_update(
            "PUT", f"https://stepik.org/api/units/{unit_id}", {"unit": fields}
        )
        self._raise_for_status(response)
        units = response.json().get("units", [])
        return units[0] if units else {}

    def list_units_for_section(self, section_id: int) -> list[dict[str, Any]]:
        """Возвращает все units секции."""
        return self._collect_paginated(
            url="https://stepik.org/api/units",
            key="units",
            params={"section": section_id},
        )

    def get_step_sources(self, lesson_id: int) -> list[dict[str, Any]]:
        """Возвращает исходники шагов урока, включая source для choice/matching."""
        return self._collect_paginated(
            url="https://stepik.org/api/step-sources",
            key="step-sources",
            params={"lesson": lesson_id},
        )

    def get_steps(self, lesson_id: int) -> list[dict[str, Any]]:
        """Возвращает обычные шаги урока через endpoint `/steps`."""
        return self._collect_paginated(
            url="https://stepik.org/api/steps",
            key="steps",
            params={"lesson": lesson_id},
        )

    def download_binary(self, url: str, *, timeout: int = 10, verify: bool = True) -> bytes:
        """Скачивает бинарный ресурс, например изображение шага."""
        if not verify:
            response = httpx.get(url, timeout=timeout, verify=False)
        else:
            response = self.client.get(url, timeout=timeout)
        response.raise_for_status()
        return response.content

    def update_step_source_block(
        self,
        step_source_id: int,
        block: dict[str, Any],
        *,
        position: int | None = None,
        cost: int | None = None,
    ) -> dict[str, Any]:
        """Обновляет block существующего step-source; при передаче position/cost фиксирует их."""
        patch: dict[str, Any] = {"block": block}
        if position is not None:
            patch["position"] = position
        if cost is not None:
            patch["cost"] = cost
        return self.update_step_source(step_source_id=step_source_id, step_source_patch=patch)

    def update_step_source_position(
        self,
        step_source_id: int,
        position: int,
        block: dict[str, Any],
    ) -> dict[str, Any]:
        """Обновляет позицию существующего step-source внутри урока."""
        return self.update_step_source(
            step_source_id=step_source_id,
            step_source_patch={"position": position, "block": block},
        )

    def delete_step_source(self, step_source_id: int) -> None:
        """Удаляет step-source из урока."""
        response = self.client.delete(
            f"https://stepik.org/api/step-sources/{step_source_id}",
            headers=self._write_headers(),
        )
        self._raise_for_status(response)

    def create_step_source(
        self,
        lesson_id: int,
        block: dict[str, Any],
        *,
        position: int | None = None,
        cost: int = 1,
    ) -> dict[str, Any]:
        """Создаёт новый step-source в существующем уроке Stepik."""
        step_source: dict[str, Any] = {
            "lesson": lesson_id,
            "block": block,
            "is_solutions_unlocked": False,
            "solutions_unlocked_attempts": 3,
            "has_submissions_restrictions": False,
            "max_submissions_count": 3,
            "cost": cost,
        }
        if position is not None:
            step_source["position"] = position

        response = self._send_json_update(
            "POST",
            "https://stepik.org/api/step-sources",
            {"step-source": step_source},
        )
        self._raise_for_status(response)
        if not response.content:
            return {}

        step_sources = response.json().get("step-sources", [])
        return step_sources[0] if step_sources else {}

    def update_step_source(
        self,
        step_source_id: int,
        step_source_patch: dict[str, Any],
    ) -> dict[str, Any]:
        """Обновляет существующий step-source через Stepik API."""
        url = f"https://stepik.org/api/step-sources/{step_source_id}"
        payload = {"step-source": step_source_patch}
        response = self._send_json_update("PATCH", url, payload)
        if response.status_code in (403, 405):
            response = self._send_json_update("PUT", url, payload)

        self._raise_for_status(response)
        if not response.content:
            return {}

        step_sources = response.json().get("step-sources", [])
        return step_sources[0] if step_sources else {}

    def _send_json_update(
        self,
        method: str,
        url: str,
        payload: dict[str, Any],
    ) -> httpx.Response:
        """Отправляет JSON-запрос на запись с авторизацией Stepik."""
        return self.client.request(method, url, headers=self._write_headers(), json=payload)

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Поднимает HTTPError с телом ответа Stepik для диагностики."""
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            response_body = response.text.strip()
            if len(response_body) > 2000:
                response_body = f"{response_body[:5000]}..."
            raise requests.HTTPError(
                f"{exc}. Response body: {response_body}",
                response=None,
            ) from exc

    def _collect_paginated(
        self,
        url: str,
        key: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Собирает все страницы endpoint'а в один список."""
        items: list[dict[str, Any]] = []
        current_url = url
        current_params = dict(params or {})

        while current_url:
            response = self.client.get(
                current_url,
                headers=self.headers,
                params=current_params or None,
            )
            response.raise_for_status()
            data = response.json()
            items.extend(data.get(key, []))

            meta = data.get("meta", {})
            next_url = meta.get("next")
            if next_url:
                current_url = next_url
                current_params = {}
                continue

            if meta.get("has_next"):
                current_url = url
                next_page = int(meta.get("page", current_params.get("page", 1))) + 1
                current_params = dict(params or {})
                current_params["page"] = next_page
                continue

            break

        return items
