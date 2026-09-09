import json
import sys
import uuid
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"
COLLECTOR_DIR = SRC_DIR / "collector"

# collector.py imports helper and parser as top-level modules.
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(COLLECTOR_DIR))

import collector as collector_module


def make_configuration(tmp_path: Path) -> dict:
    return {
        "crateName": "wombat04",
        "freshDir": str(tmp_path),
        "gpsEnable": False,
        "equipment": {
            "hostName": "pi3b",
            "hostType": "rpi3",
        },
        "geoLoc": {
            "altitude": 0,
            "latitude": 38.108,
            "longitude": -122.268,
            "siteName": "vallejo01",
        },
        "receiver": {
            "antenna": "whip",
            "receiverId": 2,
            "task": "heeler-v2-iwlist",
            "type": "ac-1300",
        },
    }


def test_init_maps_config_fields(tmp_path, monkeypatch):
    cfg = make_configuration(tmp_path)
    monkeypatch.setattr(collector_module, "configuration", cfg, raising=False)

    collector = collector_module.Collector(cfg)

    assert collector.crate_name == "wombat04"
    assert collector.fresh_dir == str(tmp_path)
    assert collector.gps_enable is False
    assert collector.host_name == "pi3b"
    assert collector.host_type == "rpi3"
    assert collector.altitude == 0
    assert collector.latitude == 38.108
    assert collector.longitude == -122.268
    assert collector.site_name == "vallejo01"
    assert collector.antenna == "whip"
    assert collector.receiver_id == 2
    assert collector.receiver_task == "heeler-v2-iwlist"
    assert collector.receiver_type == "ac-1300"


def test_copy_raw_file_copies_contents(tmp_path, monkeypatch):
    cfg = make_configuration(tmp_path)
    monkeypatch.setattr(collector_module, "configuration", cfg, raising=False)

    collector = collector_module.Collector(cfg)
    source = tmp_path / "source.raw"
    dest = tmp_path / "dest.raw"

    source.write_text("line1\nline2\n", encoding="utf-8")
    collector.copy_raw_file(str(source), str(dest))

    assert dest.exists()
    assert dest.read_text(encoding="utf-8") == "line1\nline2\n"


def test_execute_creates_json_and_raw_with_expected_payload(tmp_path, monkeypatch):
    cfg = make_configuration(tmp_path)
    monkeypatch.setattr(collector_module, "configuration", cfg, raising=False)

    collector = collector_module.Collector(cfg)

    scan_file = tmp_path / "scan.txt"
    scan_file.write_text("dummy scan content\n", encoding="utf-8")

    fixed_uuid = uuid.UUID("11111111-2222-3333-4444-555555555555")
    monkeypatch.setattr(collector_module.uuid, "uuid4", lambda: fixed_uuid)
    monkeypatch.setattr(collector_module.time, "time", lambda: 1784402415)

    observations = [
        {
            "bssid": "94:18:65:F3:3A:76",
            "frequency_mhz": 2447,
            "signal_dbm": -57,
            "ssid": "braingang2",
            "capabilities": "wpa2-psk",
            "cipher_type": "CCMP",
        }
    ]

    class FakeParser:
        def execute(self, _file_name: str):
            return observations

    monkeypatch.setattr(collector_module, "Parser", FakeParser)

    collector.execute(str(scan_file))

    raw_file = tmp_path / "11111111-2222-3333-4444-555555555555.raw"
    json_file = tmp_path / "11111111-2222-3333-4444-555555555555.json"

    assert raw_file.exists()
    assert raw_file.read_text(encoding="utf-8") == "dummy scan content\n"
    assert json_file.exists()

    payload = json.loads(json_file.read_text(encoding="utf-8"))

    assert payload["crateName"] == "wombat04"
    assert payload["fileName"] == "11111111-2222-3333-4444-555555555555.json"
    assert payload["version"] == 1
    assert payload["timeStamp"]["epochSeconds"] == 1784402415
    assert payload["timeStamp"]["iso8601"] == "2026-07-18T19:20:15+00:00"
    assert payload["observations"] == observations


def test_sample_json_shape_reference_matches_expected_keys():
    sample_path = REPO_ROOT / "samples" / "fe1e8800-97f6-43fe-b601-cbc15b4ddb93.json"
    sample = json.loads(sample_path.read_text(encoding="utf-8"))

    assert set(sample.keys()) == {
        "equipment",
        "geoLoc",
        "job",
        "timeStamp",
        "crateName",
        "fileName",
        "version",
        "observations",
    }

    first_observation = sample["observations"][0]
    assert set(first_observation.keys()) == {
        "bssid",
        "frequency_mhz",
        "signal_dbm",
        "ssid",
        "capabilities",
        "cipher_type",
    }
