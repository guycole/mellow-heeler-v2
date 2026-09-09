import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"
PECCARY_DIR = SRC_DIR / "peccary_docker"

# loader.py imports helper as a top-level package.
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(PECCARY_DIR))

import loader as loader_module


class FakePostGres:
    def __init__(self, already_processed=False, geo_loc_id=88):
        self.already_processed = already_processed
        self.geo_loc_id = geo_loc_id

        self.load_log_select_calls = []
        self.geo_loc_select_calls = []
        self.load_log_insert_payloads = []
        self.daily_score_payloads = []

        self.waps = {}
        self.next_wap_id = 100
        self.wap_insert_payloads = []

        self.observation_payloads = []
        self.bssid_score_payloads = []

    def load_log_select_by_file_name(self, file_name: str):
        self.load_log_select_calls.append(file_name)
        if self.already_processed:
            return object()
        return None

    def geo_loc_select_by_site(self, site_name: str):
        self.geo_loc_select_calls.append(site_name)
        return [SimpleNamespace(id=self.geo_loc_id)]

    def load_log_insert(self, payload: dict):
        self.load_log_insert_payloads.append(payload)
        return SimpleNamespace(id=501)

    def daily_score_insert_or_update(self, payload: dict):
        self.daily_score_payloads.append(payload)

    def _wap_key(self, wap: dict):
        return (
            wap["bssid"].lower(),
            wap["ssid"],
            wap["capability"],
            wap["cipher"],
            wap["frequency_mhz"],
        )

    def wap_select(self, wap: dict):
        key = self._wap_key(wap)
        row = self.waps.get(key)
        return [row] if row is not None else []

    def wap_select_by_bssid(self, bssid: str):
        target = bssid.lower()
        rows = [row for row in self.waps.values() if row.bssid == target]
        rows.sort(key=lambda row: row.version)
        return rows

    def wap_insert(self, payload: dict):
        row = SimpleNamespace(
            id=self.next_wap_id,
            bssid=payload["bssid"].lower(),
            ssid=payload["ssid"],
            capability=payload["capability"],
            cipher=payload["cipher"],
            frequency_mhz=payload["frequency_mhz"],
            version=payload["version"],
        )
        self.next_wap_id += 1
        self.waps[self._wap_key(payload)] = row
        self.wap_insert_payloads.append(dict(payload))
        return row

    def observation_insert(self, payload: dict):
        self.observation_payloads.append(payload)

    def bssid_score_insert_or_update(self, payload: dict):
        self.bssid_score_payloads.append(payload)


def _load_sample_json() -> dict:
    sample_file = REPO_ROOT / "samples" / "fe1e8800-97f6-43fe-b601-cbc15b4ddb93.json"
    return json.loads(sample_file.read_text(encoding="utf-8"))


def _write_json(tmp_path: Path, payload: dict, file_name: str) -> Path:
    temp = dict(payload)
    temp["fileName"] = file_name
    target = tmp_path / file_name
    target.write_text(json.dumps(temp), encoding="utf-8")
    return target


def test_file_processor_valid_sample_loads_and_removes_file(tmp_path, monkeypatch):
    payload = _load_sample_json()
    json_name = "sample-valid.json"
    _write_json(tmp_path, payload, json_name)

    failure_dir = tmp_path / "failure"
    failure_dir.mkdir()

    monkeypatch.setenv("FRESH_DIR", str(tmp_path))
    monkeypatch.setenv("FAILURE_DIR", str(failure_dir))

    fake_postgres = FakePostGres(already_processed=False, geo_loc_id=123)
    loader = loader_module.Loader(fake_postgres)

    previous_dir = os.getcwd()
    os.chdir(tmp_path)
    try:
        loader.file_processor(json_name)
    finally:
        os.chdir(previous_dir)

    assert loader.success == 1
    assert loader.failure == 0
    assert not (tmp_path / json_name).exists()

    assert fake_postgres.load_log_select_calls == [json_name]
    assert fake_postgres.geo_loc_select_calls == [payload["geoLoc"]["siteName"]]
    assert len(fake_postgres.load_log_insert_payloads) == 1
    assert len(fake_postgres.daily_score_payloads) == 1

    # Additional peccary tables: WAP, observation, and bssid score should be updated.
    assert len(fake_postgres.wap_insert_payloads) > 0
    assert len(fake_postgres.observation_payloads) == len(payload["observations"])
    assert len(fake_postgres.bssid_score_payloads) == len(payload["observations"])


def test_file_processor_mismatched_filename_moves_to_failure(tmp_path, monkeypatch):
    payload = _load_sample_json()
    json_name = "sample-mismatch.json"
    target = _write_json(tmp_path, payload, json_name)

    bad = json.loads(target.read_text(encoding="utf-8"))
    bad["fileName"] = "different-name.json"
    target.write_text(json.dumps(bad), encoding="utf-8")

    failure_dir = tmp_path / "failure"
    failure_dir.mkdir()

    monkeypatch.setenv("FRESH_DIR", str(tmp_path))
    monkeypatch.setenv("FAILURE_DIR", str(failure_dir))

    fake_postgres = FakePostGres()
    loader = loader_module.Loader(fake_postgres)

    previous_dir = os.getcwd()
    os.chdir(tmp_path)
    try:
        loader.file_processor(json_name)
    finally:
        os.chdir(previous_dir)

    assert loader.success == 0
    assert loader.failure == 1
    assert (failure_dir / json_name).exists()
    assert len(fake_postgres.load_log_insert_payloads) == 0
    assert len(fake_postgres.wap_insert_payloads) == 0
    assert len(fake_postgres.observation_payloads) == 0


def test_load_wap_creates_second_version_for_same_bssid_attribute_change(monkeypatch, tmp_path):
    monkeypatch.setenv("FRESH_DIR", str(tmp_path))
    monkeypatch.setenv("FAILURE_DIR", str(tmp_path / "failure"))

    fake_postgres = FakePostGres()
    loader = loader_module.Loader(fake_postgres)

    loader.jh.raw_json = {
        "observations": [
            {
                "bssid": "AA:BB:CC:DD:EE:FF",
                "frequency_mhz": 2412,
                "signal_dbm": -50,
                "ssid": "alpha",
                "capabilities": "wpa2-psk",
                "cipher_type": "CCMP",
            },
            {
                "bssid": "AA:BB:CC:DD:EE:FF",
                "frequency_mhz": 2412,
                "signal_dbm": -51,
                "ssid": "beta",
                "capabilities": "wpa2-psk",
                "cipher_type": "CCMP",
            },
        ]
    }

    loader.load_wap()

    assert len(fake_postgres.wap_insert_payloads) == 2
    versions = sorted([item["version"] for item in fake_postgres.wap_insert_payloads])
    assert versions == [1, 2]
