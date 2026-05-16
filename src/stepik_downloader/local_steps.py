"""Локальные HTML-шаги, изображения и ссылки на ресурсы."""

from __future__ import annotations

from pathlib import Path
import re
from typing import TYPE_CHECKING, Any

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

    def download_step_images(self, html: str, step_folder: Path) -> None:
        """Скачивает изображения из HTML в step_folder, не изменяя HTML.

        Имя файла берётся из атрибута name="..." тега <img>.
        Файл пропускается, если name отсутствует или файл уже существует.
        """
        img_pattern = re.compile(r'<img([^>]*)>', re.IGNORECASE)

        def _attr(tag_attrs: str, attr: str) -> str:
            m = re.search(rf'{attr}=["\']([^"\']*)["\']', tag_attrs, re.IGNORECASE)
            return m.group(1) if m else ""

        for match in img_pattern.finditer(html):
            tag_attrs = match.group(1)
            img_url = _attr(tag_attrs, "src")
            name_attr = _attr(tag_attrs, "name")
            if not img_url or img_url.startswith("data:") or not name_attr:
                continue
            dest = step_folder / name_attr
            if dest.exists():
                continue
            try:
                content = self.client.download_binary(img_url, timeout=10, verify=False)
                dest.write_bytes(content)
            except Exception as exc:
                print(f"WARNING: cannot download image {img_url}: {exc}")

    def extract_step_name(self, html: str, max_length: int = 100) -> str:
        """Совместимый прокси к выделенной утилите извлечения заголовка шага."""
        return extract_step_name(html, max_length=max_length)

    def save_step_html(self, step_html: str, filepath: Path | str) -> None:
        """Сохраняет HTML шага в файл."""
        Path(filepath).write_text(step_html, encoding=self.config.encoding)
