from meterweb.application.dto import BuildingCreateDTO, BuildingViewDTO, LoginDTO
from meterweb.application.ports import Authenticator, BuildingRepository
from meterweb.domain.auth import Credentials, User
from meterweb.domain.building import Building, BuildingDomainService, BuildingName


class LoginUseCase:
    def __init__(self, authenticator: Authenticator) -> None:
        self._authenticator = authenticator

    def execute(self, data: LoginDTO) -> User:
        return self._authenticator.authenticate(
            Credentials(username=data.username, password=data.password)
        )


class CreateBuildingUseCase:
    def __init__(self, repository: BuildingRepository) -> None:
        self._repository = repository

    def execute(self, data: BuildingCreateDTO) -> BuildingViewDTO:
        all_buildings = self._repository.list_all()
        names = {item.name.value.lower() for item in all_buildings}
        candidate_name = BuildingName(data.name)
        BuildingDomainService.ensure_name_is_unique(candidate_name, names)

        building = Building.create(candidate_name.value)
        self._repository.add(building)
        return BuildingViewDTO(id=building.id, name=building.name.value)


class ListBuildingsUseCase:
    def __init__(self, repository: BuildingRepository) -> None:
        self._repository = repository

    def execute(self) -> list[BuildingViewDTO]:
        return [
            BuildingViewDTO(id=item.id, name=item.name.value)
            for item in self._repository.list_all()
        ]
