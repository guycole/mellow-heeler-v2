#
# Title: loader.py
# Description: load heeler files
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
import logging
import datetime
import json
import os

from postgres import PostGres

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("loader")

class Loader:

    def __init__(self, postgres: PostGres):
        self.postgres = postgres

        self.failure_dir = os.environ.get("FAILURE_DIR", "/var/peccary/heeler/failure")
        self.fresh_dir = os.environ.get("FRESH_DIR", "/var/peccary/heeler/heeler-v2")

        self.failure = 0
        self.success = 0

    def file_failure(self, file_name: str):
        #logger.info(f"file failure:{file_name}")

        self.failure += 1
        os.rename(file_name, self.failure_dir + "/" + file_name)

    def file_success(self, file_name1: str, file_name2: str):
        #logger.info(f"file success:{file_name1}, {file_name2}")

        self.success += 1
        # must delete file
#        os.rename(file_name1, self.success_dir + "/" + file_name1)
#        os.rename(file_name2, self.success_dir + "/" + file_name2)

    def file_reader(self, file_name: str) -> bool:
        try:
            with open(file_name, "r", encoding="utf-8") as in_file:
                self.raw_buffer = json.load(in_file)
        except Exception as error:
            logger.error(f"file read failed for {file_name}: {error}")
            return False

        return True

    def load_log(self, file_name: str) -> bool:
        try:
            candidate = self.postgres.load_log_select_by_file_name(file_name)
            if candidate is not None:
                logger.info(f"skippping already processed:{file_name}")
                return False
            else:
                geo_loc = self.postgres.geo_loc_select_by_site(self.raw_buffer["geoLoc"]["siteName"])
                if len(geo_loc) == 0:
                    print("must insert geo_loc for site:", self.raw_buffer["geoLoc"]["siteName"])
                    return False
                
                # todo handle mobile or missing geoloc
                geo_loc_id = geo_loc[0].id

                candidate = {
                    "crate_name": self.raw_buffer["crate"],
                    "epoch_seconds": self.raw_buffer["timeStamp"]["epochSeconds"],
                    "file_name": file_name,
                    "file_time": self.raw_buffer["timeStamp"]["iso8601"],
                    "file_type": self.raw_buffer["project"],
                    "geo_loc_id": geo_loc_id,
                    "host_name": self.raw_buffer["equipment"]["hostName"],
                    "load_time": datetime.datetime.now(),
                    "obs_quantity": len(self.raw_buffer["observations"]),
                    "obs_time": self.raw_buffer["timeStamp"]["iso8601"],
                    "site_name": self.raw_buffer["geoLoc"]["siteName"],
                }

                self.load_log_id = self.postgres.load_log_insert(candidate).id

                daily_score = {
                    "crate_name": self.raw_buffer["crate"],
                    "file_quantity": 1,
                    "host_name": self.raw_buffer["equipment"]["hostName"],
                    "obs_quantity": len(self.raw_buffer["observations"]),
                    "score_date": datetime.date.fromisoformat(self.raw_buffer["timeStamp"]["iso8601"][:10]),
                }

                self.postgres.daily_score_insert_or_update(daily_score)

                return True
        except Exception as error:
            logger.error(f"postgres insert failed for {file_name}: {error}")
        
        return False

    def load_obs(self) -> None:
        try:
            observations = self.raw_buffer["observations"]
            for obs in observations:
                wap_id = self.postgres.wap_select(self.make_wap_from_obs(obs, 1))[0].id

                candidate = {
                    "bssid": obs["bssid"],
                    "load_log_id": self.load_log_id,
                    "obs_time": self.raw_buffer["timeStamp"]["iso8601"],
                    "signal_dbm": obs["signal_dbm"],
                    "wap_id": wap_id
                }

                self.postgres.observation_insert(candidate)
        except Exception as error:
            logger.error(f"failed to load observations: {error}")

    def make_wap_from_obs(self, obs: dict[str, any], version: int) -> dict[str, any]:
        bssid = obs["bssid"].lower()
        return {
            "bssid": bssid.strip(),
            "capability": obs["capabilities"].strip(),
            "cipher": (obs.get("cipher_type") or "stubx").strip(),
            "frequency_mhz": obs["frequency_mhz"],
            "key": f"{bssid}_{version}",
            "ssid": (obs.get("ssid") or "stubx").strip(),
            "version": version
        }
        
    def match_wap(self, wap1: dict[str, any], wap2: dict[str, any]) -> bool:
        return wap1["frequency_mhz"] == wap2["frequency_mhz"] and wap1["ssid"] == wap2["ssid"] and wap1["capability"] == wap2["capability"] and wap1["cipher"] == wap2["cipher"]
    
    def load_wap(self) -> None:
        # consolidate WAPs from observations, versioning by bssid when attributes differ
        candidates = {}

        for observation in self.raw_buffer["observations"]:
            bssid = observation["bssid"].lower()

            # gather all existing entries for this bssid
            existing = {k: v for k, v in candidates.items() if v["bssid"] == bssid}

            if not existing:
                # first occurrence of this bssid
                temp = self.make_wap_from_obs(observation, 1)
                candidates[temp["key"]] = temp
            else:
                # check if any existing version already matches this observation
                probe = self.make_wap_from_obs(observation, 0)
                if any(self.match_wap(v, probe) for v in existing.values()):
                    pass  # exact duplicate, skip
                else:
                    # distinct wap for this bssid: assign next version
                    next_version = max(v["version"] for v in existing.values()) + 1
                    temp = self.make_wap_from_obs(observation, next_version)
                    candidates[temp["key"]] = temp
                    logger.info(f"new wap version {next_version} for bssid {bssid}")

        logger.info(f"load_wap: {len(candidates)} unique WAPs from {len(self.raw_buffer['observations'])} observations")

        for candidate in candidates.values():
            try:
                selected_wap = self.postgres.wap_select(candidate)
                if len(selected_wap) < 1:
                    # no exact match in DB — find the max version already stored for this bssid
                    db_versions = self.postgres.wap_select_by_bssid(candidate["bssid"])
                    if db_versions:
                        candidate["version"] = max(w.version for w in db_versions) + 1
                        candidate["key"] = f"{candidate['bssid']}_{candidate['version']}"
                    self.postgres.wap_insert(candidate)
            except Exception as error:
                logger.error(f"failed to load wap: {error}")

    def file_processor(self, file_name) -> None:
        if os.path.isfile(file_name) is False:
            logger.warning(f"skipping non-file:{file_name}")
            self.file_failure(file_name)
            return

        if not file_name.endswith(".json"):
            logger.warning(f"skipping non-json:{file_name}")
            self.file_failure(file_name)
            return

        if not self.file_reader(file_name):
            logger.warning(f"file read failed for {file_name}")
            self.file_failure(file_name)
            return

        if self.raw_buffer["version"] == 1 and self.raw_buffer["project"] == "heeler-v2":
            pass
        else:
            logger.warning(f"invalid version or project for {file_name}")
            self.file_failure(file_name)
            return
        
        if self.load_log(file_name):
            self.load_wap()
            self.load_obs()
        else:
            self.file_failure(file_name)

    def execute(self) -> None:
        logger.info("loader")
        logger.info(f"fresh dir:{self.fresh_dir}")

        os.chdir(self.fresh_dir)
        targets = sorted(os.listdir("."))
        logger.info(f"{len(targets)} files noted")

        for target in targets:
            self.file_processor(target)

        logger.info(f"validator success:{self.success} failure:{self.failure}")

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
