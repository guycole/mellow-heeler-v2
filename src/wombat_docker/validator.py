#
# Title: validator.py
# Description: ensure valid heeler files
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
import logging
import datetime
import json
import os

from postgres import PostGres

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("heeler")

class Validator:

    def __init__(self, postgres: PostGres):
        self.postgres = postgres

        self.failure_dir = os.environ.get("FAILURE_DIR", "/var/wombat/failure")
        self.fresh_dir = os.environ.get("FRESH_DIR", "/var/wombat/fresh/heeler")
        self.success_dir = os.environ.get("SUCCESS_DIR", "/var/wombat/heeler/success")

        self.failure = 0
        self.success = 0

    def file_failure(self, file_name: str):
        logger.info(f"file failure:{file_name}")

        self.failure += 1
        os.rename(file_name, self.failure_dir + file_name)

    def file_success(self, file_name1: str, file_name2: str):
        #logger.info(f"file success:{file_name1}, {file_name2}")

        self.success += 1
        os.rename(file_name1, self.success_dir + "/" + file_name1)
        os.rename(file_name2, self.success_dir + "/" + file_name2)

    def file_reader(self, file_name: str) -> bool:
        try:
            with open(file_name, "r", encoding="utf-8") as in_file:
                self.raw_buffer = json.load(in_file)
        except Exception as error:
            logger.error(f"file read failed for {file_name}: {error}")
            return False

        return True

    def load_log_test(self, test_file_name: str) -> bool:
        logger.info(f"load_log_test for file: {test_file_name}")

        try:
            candidate = self.postgres.load_log_select_by_file_name(test_file_name)
            if candidate is None:
                logger.info(f"processing new file:{test_file_name}")

                geo_loc = self.postgres.geo_loc_select_by_site(self.raw_buffer["geoLoc"]["siteName"])
                if len(geo_loc) == 0:
                    print("must insert geo_loc for site:", self.raw_buffer["geoLoc"]["siteName"])
                    return False

                load_log = {
                    "crate_name": self.raw_buffer["crate"],
                    "epoch_seconds": self.raw_buffer["timeStamp"]["epochSeconds"],
                    "file_name": test_file_name,                   
                    "geo_loc_id": geo_loc[0].id,
                    "host_name": self.raw_buffer["equipment"]["hostName"],
                    "load_time": datetime.datetime.now(),
                    "mode": self.raw_buffer["job"]["mode"],
                    "obs_quantity": len(self.raw_buffer["observations"]),
                    "obs_time": self.raw_buffer["timeStamp"]["iso8601"],
                    "site_name": self.raw_buffer["geoLoc"]["siteName"],
                    "task": self.raw_buffer["job"]["task"],
                }

                self.postgres.load_log_insert(load_log)

                daily_score = {
                    "crate_name": self.raw_buffer["crate"],
                    "file_quantity": 1,
                    "host_name": self.raw_buffer["equipment"]["hostName"],
                    "obs_quantity": len(self.raw_buffer["observations"]),
                    "score_date": datetime.date.fromisoformat(self.raw_buffer["timeStamp"]["iso8601"][:10]),
                }

                self.postgres.daily_score_insert_or_update(daily_score)

                return True
            else:
                logger.info(f"skippping already processed:{test_file_name}")
                print("skipping already processed file")
                return False

        except Exception as error:
            logger.error(f"postgres failure {test_file_name}: {error}")        
        
        return False

    def file_processor(self, file_name1: str, file_name2: str) -> None:
        if os.path.isfile(file_name1) is False:
            logger.warning(f"skipping non-file:{file_name1}")
            self.file_failure(file_name1)
            self.file_failure(file_name2)
            return

        if os.path.isfile(file_name2) is False:
            logger.warning(f"skipping non-file:{file_name2}")
            self.file_failure(file_name1)
            self.file_failure(file_name2)
            return
        
        test_file_name = file_name1 if file_name1.endswith(".json") else file_name2
        if not self.file_reader(test_file_name):
            logger.warning(f"file read failed for {test_file_name}")
            self.file_failure(file_name1)
            self.file_failure(file_name2)
            return

        if self.raw_buffer["version"] == 1 and self.raw_buffer["job"]["project"] == "heeler-v2":
            pass
        else:
            logger.warning(f"invalid version or project for {test_file_name}")
            self.file_failure(file_name1)
            self.file_failure(file_name2)
            return
        
        if self.load_log_test(test_file_name):
            self.file_success(file_name1, file_name2)
        else:
            self.file_failure(file_name1)
            self.file_failure(file_name2)

    def execute(self) -> None:
        logger.info("validator")
        logger.info(f"fresh dir:{self.fresh_dir}")

        os.chdir(self.fresh_dir)
        targets = sorted(os.listdir("."))
        logger.info(f"{len(targets)} files noted")

        ndx1 = 0
        while ndx1 < len(targets)-1:
            # valid files will arrive in pairs
            target1 = targets[ndx1]
            target2 = targets[ndx1+1]

            temp = target1.split(".")
            if target2.startswith(temp[0]):
                self.file_processor(target1, target2)
                ndx1 += 1
            else:
                self.file_failure(target1)

            ndx1 += 1

        logger.info(f"validator success:{self.success} failure:{self.failure}")

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
