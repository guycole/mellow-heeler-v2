#
# Title: loader.py
# Description: load heeler files
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
import logging
import datetime
import os
from abc import ABC, abstractmethod

from typing import Any

from helper.json_helper import JsonHelper

from helper.postgres import PostGres

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("loader")


class LoaderBase(ABC):
    @abstractmethod
    def file_processor(self, file_name: str) -> bool:
        pass

    @abstractmethod
    def execute(self) -> int:
        pass

    @abstractmethod
    def file_failure(self, file_name: str) -> None:
        pass

    @abstractmethod
    def file_success(self, file_name: str) -> None:
        pass

    @abstractmethod
    def load_log_test(self, test_file_name: str) -> bool:
        pass


class HeelerLoader(LoaderBase):

    def __init__(self, logger_instance: logging.Logger, postgres: PostGres):
        self.logger = logger_instance
        self.postgres = postgres

        self.failure_dir = os.environ.get("FAILURE_DIR", "/var/peccary/heeler/failure")
        self.fresh_dir = os.environ.get("FRESH_DIR", "/var/peccary/heeler/heeler-v2")

        self.failure = 0
        self.success = 0

        self.json_helper = JsonHelper(self.logger)
        self.jh = self.json_helper
        self.load_log_id: int | None = None

    def file_failure(self, file_name: str) -> None:
        self.failure += 1
        failure_target = os.path.join(self.failure_dir, file_name)
        try:
            os.rename(file_name, failure_target)
        except OSError as error:
            self.logger.error(
                "file move failure for %s -> %s: %s", file_name, failure_target, error
            )

    def file_success(self, file_name: str) -> None:
        self.success += 1
        try:
            os.remove(file_name)
        except OSError as error:
            self.logger.error("file delete failure for %s: %s", file_name, error)

    def load_log_test(self, test_file_name: str) -> bool:
        try:
            candidate = self.postgres.load_log_select_by_file_name(test_file_name)
            if candidate is not None:
                self.logger.info("skipping already processed:%s", test_file_name)
                return False

            raw_json = self.json_helper.raw_json
            geo_loc = self.postgres.geo_loc_select_by_site(raw_json["geoLoc"]["siteName"])
            if len(geo_loc) == 0:
                self.logger.error(
                    "must insert geo_loc for site: %s", raw_json["geoLoc"]["siteName"]
                )
                return False

            load_log = {
                "crate_name": raw_json["crateName"],
                "epoch_seconds": raw_json["timeStamp"]["epochSeconds"],
                "file_name": test_file_name,
                "geo_loc_id": geo_loc[0].id,
                "host_name": raw_json["equipment"]["hostName"],
                "load_time": datetime.datetime.now(),
                "mode": raw_json["job"]["mode"],
                "obs_quantity": len(raw_json["observations"]),
                "obs_time": raw_json["timeStamp"]["iso8601"],
                "site_name": raw_json["geoLoc"]["siteName"],
                "source_file_name": raw_json.get("sourceFileName", test_file_name),
                "task": raw_json["job"]["task"],
            }

            self.load_log_id = self.postgres.load_log_insert(load_log).id

            daily_score = {
                "crate_name": raw_json["crateName"],
                "file_quantity": 1,
                "host_name": raw_json["equipment"]["hostName"],
                "obs_quantity": len(raw_json["observations"]),
                "score_date": datetime.date.fromisoformat(
                    raw_json["timeStamp"]["iso8601"][:10]
                ),
            }

            self.postgres.daily_score_insert_or_update(daily_score)
            return True
        except Exception as error:
            self.logger.error(
                "postgres insert failed for %s: %s", test_file_name, error
            )

        return False

    def _obs_value(self, observation: dict[str, Any], *keys: str, default: Any = None) -> Any:
        for key in keys:
            if key in observation:
                return observation[key]
        return default

    def load_obs(self) -> None:
        if self.load_log_id is None:
            self.logger.error("load_log_id missing, skipping observations")
            return

        try:
            observations = self.json_helper.raw_json["observations"]
            for obs in observations:
                wap_id = self.postgres.wap_select(self.make_wap_from_obs(obs, 1))[0].id

                candidate = {
                    "bssid": obs["bssid"],
                    "load_log_id": self.load_log_id,
                    "obs_time": self.json_helper.raw_json["timeStamp"]["iso8601"],
                    "signal_dbm": self._obs_value(obs, "signal_dbm", "signalDbm", default=0),
                    "wap_id": wap_id,
                }

                self.postgres.observation_insert(candidate)

                bssid_score = {
                    "bssid": obs["bssid"],
                    "quantity": 1,
                }

                self.postgres.bssid_score_insert_or_update(bssid_score)
        except Exception as error:
            self.logger.error("failed to load observations: %s", error)

    def make_wap_from_obs(self, obs: dict[str, Any], version: int) -> dict[str, Any]:
        bssid = obs["bssid"].lower()
        return {
            "bssid": bssid.strip(),
            "capability": str(obs.get("capabilities", "")).strip(),
            "cipher": str(self._obs_value(obs, "cipher_type", "cipherType", default="xstubx")).strip(),
            "frequency_mhz": int(self._obs_value(obs, "frequency_mhz", "frequencyMhz", default=0)),
            "key": f"{bssid}_{version}",
            "ssid": str(obs.get("ssid") or "xstubx").strip(),
            "version": version,
        }

    def match_wap(self, wap1: dict[str, Any], wap2: dict[str, Any]) -> bool:
        return (
            wap1["frequency_mhz"] == wap2["frequency_mhz"]
            and wap1["ssid"] == wap2["ssid"]
            and wap1["capability"] == wap2["capability"]
            and wap1["cipher"] == wap2["cipher"]
        )

    def load_wap(self) -> None:
        candidates: dict[str, dict[str, Any]] = {}

        for observation in self.json_helper.raw_json["observations"]:
            bssid = observation["bssid"].lower()
            existing = {k: v for k, v in candidates.items() if v["bssid"] == bssid}

            if not existing:
                temp = self.make_wap_from_obs(observation, 1)
                candidates[temp["key"]] = temp
                continue

            probe = self.make_wap_from_obs(observation, 0)
            if any(self.match_wap(v, probe) for v in existing.values()):
                continue

            next_version = max(v["version"] for v in existing.values()) + 1
            temp = self.make_wap_from_obs(observation, next_version)
            candidates[temp["key"]] = temp
            self.logger.info("new wap version %s for bssid %s", next_version, bssid)

        self.logger.info(
            "load_wap: %s unique WAPs from %s observations",
            len(candidates),
            len(self.json_helper.raw_json["observations"]),
        )

        for candidate in candidates.values():
            try:
                selected_wap = self.postgres.wap_select(candidate)
                if len(selected_wap) < 1:
                    db_versions = self.postgres.wap_select_by_bssid(candidate["bssid"])
                    if db_versions:
                        candidate["version"] = max(w.version for w in db_versions) + 1
                        candidate["key"] = f"{candidate['bssid']}_{candidate['version']}"
                    self.postgres.wap_insert(candidate)
            except Exception as error:
                self.logger.error("failed to load wap: %s", error)

    def file_processor(self, file_name: str) -> bool:
        self.logger.info("processing file: %s", file_name)

        if not os.path.isfile(file_name):
            self.logger.warning("skipping non-file:%s", file_name)
            self.file_failure(file_name)
            return False

        if not file_name.endswith(".json"):
            self.logger.warning("skipping non-json:%s", file_name)
            self.file_failure(file_name)
            return False

        if not self.json_helper.json_file_reader(file_name, False):
            self.logger.warning("json file read failure for %s", file_name)
            self.file_failure(file_name)
            return False

        payload_file_name = self.json_helper.raw_json.get("fileName", "")
        if os.path.basename(payload_file_name) != os.path.basename(file_name):
            self.logger.warning(
                "mismatched file name: %s vs %s", payload_file_name, file_name
            )
            self.file_failure(file_name)
            return False

        if (
            self.json_helper.raw_json.get("version") != 1
            or self.json_helper.raw_json.get("job", {}).get("project")
            != "heeler-v2"
        ):
            self.logger.warning("invalid version or project for %s", file_name)
            self.file_failure(file_name)
            return False

        if self.load_log_test(file_name):
            self.load_wap()
            self.load_obs()
            self.file_success(file_name)
            return True

        self.file_failure(file_name)
        return False

    def execute(self) -> int:
        self.logger.info("loader fresh dir:%s", self.fresh_dir)

        os.chdir(self.fresh_dir)
        targets = sorted(os.listdir("."))
        self.logger.info("%s files noted", len(targets))

        for target in targets:
            self.file_processor(target)

        self.logger.info("loader success:%s failure:%s", self.success, self.failure)
        return 0


class Loader(HeelerLoader):
    """Compatibility alias for existing imports/tests."""

    def __init__(self, postgres: PostGres):
        super().__init__(logger, postgres)


# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
