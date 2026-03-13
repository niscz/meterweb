from abc import ABC, abstractmethod


class ReportRenderer(ABC):
    @abstractmethod
    def render_pdf(self, html: str) -> bytes:
        raise NotImplementedError
