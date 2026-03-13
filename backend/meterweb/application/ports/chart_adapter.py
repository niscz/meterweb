from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ChartSeries:
    name: str
    values: list[float]


@dataclass(frozen=True)
class ChartSchema:
    title: str
    categories: list[str]
    series: list[ChartSeries] = field(default_factory=list)


class ChartAdapter(ABC):
    @abstractmethod
    def render_config(self, chart: ChartSchema) -> dict:
        raise NotImplementedError
