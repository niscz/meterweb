import json
from uuid import uuid4

from meterweb.infrastructure.repositories import JsonWeatherStationRepository


def test_load_returns_empty_dict_for_invalid_json(tmp_path, caplog) -> None:
    storage_file = tmp_path / "weather_overrides.json"
    storage_file.write_text("{invalid json", encoding="utf-8")
    repository = JsonWeatherStationRepository(storage_file)

    building_id = uuid4()

    assert repository.get_override(building_id) is None
    assert f"{storage_file}" in caplog.text


def test_set_override_writes_and_removes_entries_atomically(tmp_path) -> None:
    storage_file = tmp_path / "weather_overrides.json"
    repository = JsonWeatherStationRepository(storage_file)

    building_id = uuid4()

    repository.set_override(building_id, "station-123")
    assert json.loads(storage_file.read_text(encoding="utf-8")) == {str(building_id): "station-123"}

    repository.set_override(building_id, None)
    assert json.loads(storage_file.read_text(encoding="utf-8")) == {}
