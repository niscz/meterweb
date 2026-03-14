from pathlib import Path
import json

import pytest
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


def test_set_override_cleans_up_temp_file_when_replace_fails(tmp_path, monkeypatch) -> None:
    storage_file = tmp_path / "weather_overrides.json"
    repository = JsonWeatherStationRepository(storage_file)

    def _raise_replace(self, target):
        raise OSError("replace failed")

    monkeypatch.setattr(Path, "replace", _raise_replace)

    building_id = uuid4()

    temp_files_before = set(tmp_path.iterdir())
    with pytest.raises(OSError, match="replace failed"):
        repository.set_override(building_id, "station-123")

    temp_files_after = set(tmp_path.iterdir())
    assert temp_files_after == temp_files_before
