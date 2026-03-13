import pytest

from meterweb.domain.building import BuildingDomainService, BuildingName


def test_building_name_must_not_be_empty() -> None:
    with pytest.raises(ValueError):
        BuildingName("   ")


def test_building_name_must_be_unique_case_insensitive() -> None:
    with pytest.raises(ValueError):
        BuildingDomainService.ensure_name_is_unique(BuildingName("HQ"), {"hq"})
