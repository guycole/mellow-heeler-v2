import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"
WOMBAT_DIR = SRC_DIR / "wombat_docker"

# validator.py imports helper as top-level package.
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(WOMBAT_DIR))

import validator as validator_module


class FakePostGres:
    def __init__(self, already_processed=False, geo_loc_id=77):
        self.already_processed = already_processed
        self.geo_loc_id = geo_loc_id

        self.load_log_select_calls = []
        self.geo_loc_select_calls = []
        self.load_log_insert_payloads = []
        self.daily_score_payloads = []

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

    def daily_score_insert_or_update(self, payload: dict):
        self.daily_score_payloads.append(payload)


def _load_sample_json() -> dict:
    sample_file = REPO_ROOT / "samples" / "fe1e8800-97f6-43fe-b601-cbc15b4ddb93.json"
    return json.loads(sample_file.read_text(encoding="utf-8"))


def _write_test_pair(tmp_path: Path, payload: dict, base_name: str):
    json_name = f"{base_name}.json"
    raw_name = f"{base_name}.raw"

    payload = dict(payload)
    payload["fileName"] = json_name

    (tmp_path / json_name).write_text(json.dumps(payload), encoding="utf-8")
    (tmp_path / raw_name).write_text("raw data\n", encoding="utf-8")

    return json_name, raw_name


def _make_dirs(tmp_path: Path):
    fresh_dir = tmp_path
    success_dir = tmp_path / "success"
    failure_dir = tmp_path / "failure"
    success_dir.mkdir()
    failure_dir.mkdir()
    return fresh_dir, success_dir, failure_dir


def test_file_processor_valid_pair_writes_postgres_and_moves_to_success(tmp_path, monkeypatch):
    payload = _load_sample_json()
    json_name, raw_name = _write_test_pair(tmp_path, payload, "scan-valid")
    fresh_dir, success_dir, failure_dir = _make_dirs(tmp_path)

    monkeypatch.setenv("FRESH_DIR", str(fresh_dir))
    monkeypatch.setenv("SUCCESS_DIR", str(success_dir))
    monkeypatch.setenv("FAILURE_DIR", str(failure_dir))

    fake_postgres = FakePostGres(already_processed=False, geo_loc_id=123)
    validator = validator_module.Validator(fake_postgres)

    previous_dir = os.getcwd()
    os.chdir(tmp_path)
    try:
        validator.file_processor(json_name, raw_name)
    finally:
        os.chdir(previous_dir)

    assert validator.success == 1
    assert validator.failure == 0
    assert not (tmp_path / json_name).exists()
    assert not (tmp_path / raw_name).exists()
    assert (success_dir / json_name).exists()
    assert (success_dir / raw_name).exists()

    assert fake_postgres.load_log_select_calls == [json_name]
    assert fake_postgres.geo_loc_select_calls == [payload["geoLoc"]["siteName"]]
    assert len(fake_postgres.load_log_insert_payloads) == 1
    assert len(fake_postgres.daily_score_payloads) == 1

    load_log = fake_postgres.load_log_insert_payloads[0]
    assert load_log["crate_name"] == payload["crateName"]
    assert load_log["host_name"] == payload["equipment"]["hostName"]
    assert load_log["obs_quantity"] == len(payload["observations"])
    assert load_log["geo_loc_id"] == 123


def test_file_processor_mismatched_json_filename_moves_to_failure(tmp_path, monkeypatch):
    payload = _load_sample_json()
    json_name, raw_name = _write_test_pair(tmp_path, payload, "scan-mismatch")
    fresh_dir, success_dir, failure_dir = _make_dirs(tmp_path)

    # Force mismatch between payload and actual test file name.
    bad_payload = json.loads((tmp_path / json_name).read_text(encoding="utf-8"))
    bad_payload["fileName"] = "other-file.json"
    (tmp_path / json_name).write_text(json.dumps(bad_payload), encoding="utf-8")

    monkeypatch.setenv("FRESH_DIR", str(fresh_dir))
    monkeypatch.setenv("SUCCESS_DIR", str(success_dir))
    monkeypatch.setenv("FAILURE_DIR", str(failure_dir))

    fake_postgres = FakePostGres(already_processed=False)
    validator = validator_module.Validator(fake_postgres)

    previous_dir = os.getcwd()
    os.chdir(tmp_path)
    try:
        validator.file_processor(json_name, raw_name)
    finally:
        os.chdir(previous_dir)

    assert validator.success == 0
    assert validator.failure == 2
    assert (failure_dir / json_name).exists()
    assert (failure_dir / raw_name).exists()
    assert len(fake_postgres.load_log_insert_payloads) == 0
    assert len(fake_postgres.daily_score_payloads) == 0


def test_file_processor_duplicate_file_moves_to_failure_without_new_inserts(tmp_path, monkeypatch):
    payload = _load_sample_json()
    json_name, raw_name = _write_test_pair(tmp_path, payload, "scan-duplicate")
    fresh_dir, success_dir, failure_dir = _make_dirs(tmp_path)

    monkeypatch.setenv("FRESH_DIR", str(fresh_dir))
    monkeypatch.setenv("SUCCESS_DIR", str(success_dir))
    monkeypatch.setenv("FAILURE_DIR", str(failure_dir))

    fake_postgres = FakePostGres(already_processed=True)
    validator = validator_module.Validator(fake_postgres)

    previous_dir = os.getcwd()
    os.chdir(tmp_path)
    try:
        validator.file_processor(json_name, raw_name)
    finally:
        os.chdir(previous_dir)

    assert validator.success == 0
    assert validator.failure == 2
    assert (failure_dir / json_name).exists()
    assert (failure_dir / raw_name).exists()
    assert len(fake_postgres.load_log_insert_payloads) == 0
    assert len(fake_postgres.daily_score_payloads) == 0
