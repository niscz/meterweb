from abc import ABC, abstractmethod
from typing import Any


class ReportRenderer(ABC):
    @abstractmethod
    def render_pdf_template(self, template_path: str, context: dict[str, Any]) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def render_xlsx(self, rows: list[dict[str, str]]) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def render_csv(self, rows: list[dict[str, str]]) -> bytes:
        raise NotImplementedError
