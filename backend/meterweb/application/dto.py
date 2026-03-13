from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class LoginDTO:
    username: str
    password: str


@dataclass(frozen=True, slots=True)
class BuildingCreateDTO:
    name: str


@dataclass(frozen=True, slots=True)
class BuildingViewDTO:
    id: UUID
    name: str
