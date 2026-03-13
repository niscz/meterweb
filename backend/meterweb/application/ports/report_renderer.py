from abc import ABC, abstractmethod


class ReportRenderer(ABC):
    @abstractmethod
    def render_pdf(self, html: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def render_xlsx(self, rows: list[dict[str, str]]) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def render_csv(self, rows: list[dict[str, str]]) -> bytes:
        raise NotImplementedError
