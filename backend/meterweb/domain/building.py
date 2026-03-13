from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class BuildingName:
    value: str

    def __post_init__(self) -> None:
        cleaned = self.value.strip()
        if not cleaned:
            raise ValueError("Gebäudename darf nicht leer sein.")
        object.__setattr__(self, "value", cleaned)


@dataclass(frozen=True, slots=True)
class Building:
    id: UUID
    name: BuildingName

    @classmethod
    def create(cls, name: str) -> "Building":
        return cls(id=uuid4(), name=BuildingName(name))


class BuildingDomainService:
    @staticmethod
    def ensure_name_is_unique(name: BuildingName, existing_names: set[str]) -> None:
        if name.value.lower() in existing_names:
            raise ValueError("Gebäudename existiert bereits.")
