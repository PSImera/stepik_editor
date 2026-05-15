"""Локальные HTML-шаги, изображения и ссылки на ресурсы."""

from __future__ import annotations

from pathlib import Path
import re
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from .html_utils import extract_step_name

if TYPE_CHECKING:
    from ..config import EditorConfig
    from .api import StepikAPIClient


class LocalStepsMixin:
    if TYPE_CHECKING:
        client: StepikAPIClient
        config: EditorConfig

    def _get_local_html_step_files(
        self,
        lesson_folder: Path,
        section_num: int,
        lesson_num: int,
    ) -> dict[int, Path]:
        """Возвращает локальные HTML-файлы урока по номерам шагов."""
        prefix = f"{section_num:02d}-{lesson_num:02d}-"
        step_file_pattern = re.compile(
            rf"^{section_num:02d}-{lesson_num:02d}-(\d+)\.html$"
        )
        local_step_files: dict[int, Path] = {}

        for step_filepath in sorted(lesson_folder.glob(f"{prefix}*.html")):
            match = step_file_pattern.match(step_filepath.name)
            if match is None:
                continue

            local_step_files[int(match.group(1))] = step_filepath

        return local_step_files

    def _build_text_step_block(self, step_html: str) -> dict[str, Any]:
        """Собирает минимальный Stepik block для нового текстового шага."""
        return {"name": "text", "text": self._strip_html_comments(step_html)}

    @staticmethod
    def _strip_html_comments(html: str) -> str:
        """Удаляет HTML-комментарии перед отправкой — они не нужны на Stepik."""
        import re
        return re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL).strip()

    def _get_step_html_filepath(
        self,
        lesson_folder: Path,
        section_num: int,
        lesson_num: int,
        step_num: int,
    ) -> Path:
        """Возвращает путь к локальному HTML-файлу шага."""
        return lesson_folder / f"{section_num:02d}-{lesson_num:02d}-{step_num:02d}.html"

    def read_step_html(self, filepath: Path | str) -> str:
        """Читает локальный HTML-файл шага как UTF-8/encoding из конфига."""
        html = Path(filepath).read_text(encoding=self.config.encoding).strip()
        body_match = re.search(
            r"<body[^>]*>(.*?)</body>",
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if body_match is not None:
            return body_match.group(1).strip()

        return html

    def find_local_asset_references(self, html: str) -> list[str]:
        """Находит относительные src/href, которые Stepik не сможет открыть сам."""
        references: list[str] = []
        for match in re.finditer(
            r"\b(?:src|href)=['\"]([^'\"]+)['\"]",
            html,
            flags=re.IGNORECASE,
        ):
            value = match.group(1).strip()
            if not value:
                continue
            if value.startswith(("#", "//", "http://", "https://")):
                continue
            if value.startswith(("data:", "mailto:", "tel:")):
                continue
            references.append(value)
        return references

    def _print_local_asset_warning(self, step_num: int, step_html: str) -> None:
        """Печатает предупреждение про локальные ссылки, которые Stepik не загрузит."""
        asset_refs = self.find_local_asset_references(step_html)
        if not asset_refs:
            return

        preview = ", ".join(asset_refs[:3])
        suffix = "..." if len(asset_refs) > 3 else ""
        print(
            f"    Шаг {step_num}: есть локальные ссылки на файлы "
            f"({preview}{suffix}); они будут отправлены как есть"
        )

    def download_images(self, html: str, step_folder: Path) -> str:
        """Скачивает изображения из HTML шага в step_folder, нумеруя 01, 02, ...

        Ссылки в HTML заменяются на имя файла (без пути — файл лежит рядом с task.html).
        """
        counter = 0
        img_pattern = re.compile(
            r'(<img[^>]+src=["\'])([^"\']+)(["\'][^>]*>)',
            re.IGNORECASE,
        )

        def replace_img(match: re.Match[str]) -> str:
            nonlocal counter
            prefix, img_url, suffix = match.group(1), match.group(2), match.group(3)
            if img_url.startswith("data:"):
                return match.group(0)
            try:
                content = self.client.download_binary(img_url, timeout=10, verify=False)
                ext = Path(urlparse(img_url).path).suffix or ".jpg"
                counter += 1
                filename = f"{counter:02d}{ext}"
                (step_folder / filename).write_bytes(content)
                return f"{prefix}{filename}{suffix}"
            except Exception as exc:
                print(f"WARNING: cannot download image {img_url}: {exc}")
                return f"<!-- image unavailable: {img_url} -->"

        return img_pattern.sub(replace_img, html)

    def extract_step_name(self, html: str, max_length: int = 100) -> str:
        """Совместимый прокси к выделенной утилите извлечения заголовка шага."""
        return extract_step_name(html, max_length=max_length)

    def save_step_html(self, step_html: str, filepath: Path | str) -> None:
        """Сохраняет HTML шага в отдельный файл с учётом настроек конфига."""
        if self.config.html_head:
            full_html = f"""<html>
<head>
    <meta charset='{self.config.encoding}'>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        img {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
{step_html}
</body>
</html>"""
        else:
            full_html = step_html

        Path(filepath).write_text(full_html, encoding=self.config.encoding)
