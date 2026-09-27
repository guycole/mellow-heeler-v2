#
# Title: validator.py
# Description: ensure valid heeler files
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
import logging
import datetime
import os
from abc import ABC, abstractmethod

from helper.json_helper import JsonHelper

from helper.postgres import PostGres

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("validator")


class Validator(ABC):
    @abstractmethod
    def file_failure(self, file_name: str) -> None:
        pass

    @abstractmethod
    def file_failure2(self, file_name1: str, file_name2: str) -> None:
        pass

    @abstractmethod
    def file_success2(self, file_name1: str, file_name2: str) -> None:
        pass

    @abstractmethod
    def load_log_test(self, test_file_name: str) -> bool:
        pass

    @abstractmethod
    def file_processor(self, file_name1: str, file_name2: str) -> None:
        pass

    @abstractmethod
    def execute(self) -> int:
        pass


class HeelerValidator(Validator):

    def __init__(
        self,
        logger_or_postgres: logging.Logger | PostGres,
        postgres: PostGres | None = None,
    ):
        if postgres is None:
            self.logger = logger
            self.postgres = logger_or_postgres
        else:
            self.logger = logger_or_postgres
            self.postgres = postgres

        self.failure_dir = os.environ.get("FAILURE_DIR", "/var/wombat/failure")
        self.fresh_dir = os.environ.get("FRESH_DIR", "/var/wombat/fresh/heeler")
        self.success_dir = os.environ.get("SUCCESS_DIR", "/var/wombat/heeler/success")

        self.failure = 0
        self.success = 0

        self.json_helper = JsonHelper(self.logger)

    def _group_pairs(
        self, targets: list[str]
    ) -> tuple[list[tuple[str, str]], list[str]]:
        grouped = {}
        for target in targets:
            stem, _, _ = target.partition(".")
            grouped.setdefault(stem, []).append(target)

        pairs: list[tuple[str, str]] = []
        orphans: list[str] = []

        for stem in sorted(grouped.keys()):
            members = sorted(grouped[stem])
            json_files = [item for item in members if item.endswith(".json")]
            non_json_files = [item for item in members if not item.endswith(".json")]

            if len(json_files) == 1 and len(non_json_files) == 1:
                pairs.append((json_files[0], non_json_files[0]))
            else:
                self.logger.warning("invalid file pair for stem:%s files:%s", stem, members)
                orphans.extend(members)

        return pairs, sorted(orphans)

    def file_failure(self, file_name: str) -> None:
        self.logger.info("file failure:%s", file_name)

        self.failure += 1
        failure_target = os.path.join(self.failure_dir, file_name)
        try:
            os.rename(file_name, failure_target)
        except OSError as error:
            self.logger.error(
                "file move failure for %s -> %s: %s", file_name, failure_target, error
            )

    def file_failure2(self, file_name1: str, file_name2: str) -> None:
        self.file_failure(file_name1)
        self.file_failure(file_name2)

    def file_success2(self, file_name1: str, file_name2: str) -> None:
        self.success += 1
        success_target1 = os.path.join(self.success_dir, file_name1)
        success_target2 = os.path.join(self.success_dir, file_name2)
        try:
            os.rename(file_name1, success_target1)
            os.rename(file_name2, success_target2)
        except OSError as error:
            self.logger.error(
                "file move success-target failure for %s/%s: %s",
                file_name1,
                file_name2,
                error,
            )

    def load_log_test(self, test_file_name: str) -> bool:
        self.logger.info("load_log_test for file: %s", test_file_name)

        try:
            candidate = self.postgres.load_log_select_by_file_name(test_file_name)
            if candidate is None:
                self.logger.info("processing new file:%s", test_file_name)

                geo_loc = self.postgres.geo_loc_select_by_site(
                    self.json_helper.raw_json["geoLoc"]["siteName"]
                )
                if len(geo_loc) == 0:
                    self.logger.error(
                        "must insert geo_loc for site: %s",
                        self.json_helper.raw_json["geoLoc"]["siteName"],
                    )
                    return False

                load_log = {
                    "crateName": self.json_helper.raw_json["crateName"],
                    "epochSeconds": self.json_helper.raw_json["timeStamp"]["epochSeconds"],
                    "fileName": test_file_name,
                    "geoLocId": geo_loc[0].id,
                    "hostName": self.json_helper.raw_json["equipment"]["hostName"],
                    "loadTime": datetime.datetime.now(),
                    "mode": self.json_helper.raw_json["job"]["mode"],
                    "obsQuantity": len(self.json_helper.raw_json["observations"]),
                    "obsTime": self.json_helper.raw_json["timeStamp"]["iso8601"],
                    "siteName": self.json_helper.raw_json["geoLoc"]["siteName"],
                    "sourceFileName": self.json_helper.raw_json["sourceFileName"],
                    "task": self.json_helper.raw_json["job"]["task"],
                }

                self.postgres.load_log_insert(load_log)

                daily_score = {
                    "crateName": self.json_helper.raw_json["crateName"],
                    "fileQuantity": 1,
                    "hostName": self.json_helper.raw_json["equipment"]["hostName"],
                    "obsQuantity": len(self.json_helper.raw_json["observations"]),
                    "scoreDate": datetime.date.fromisoformat(
                        self.json_helper.raw_json["timeStamp"]["iso8601"][:10]
                    ),
                }

                self.postgres.daily_score_insert_or_update(daily_score)

                if len(self.json_helper.raw_json["observations"]) < 1:
                    self.logger.info("skipping file with no observations")
                    return False

                return True
            else:
                self.logger.info("skippping already processed:%s", test_file_name)
                return False

        except (KeyError, TypeError, ValueError, OSError) as error:
            self.logger.error("postgres failure %s: %s", test_file_name, error)

        return False

    def file_processor(self, file_name1: str, file_name2: str) -> None:
        self.logger.info("processing files: %s, %s", file_name1, file_name2)

        test_file_name = file_name1 if file_name1.endswith(".json") else file_name2
        if not self.json_helper.json_file_tester(test_file_name, "heeler-v2", 2):
            self.file_failure2(file_name1, file_name2)
            return

        if self.load_log_test(test_file_name):
            self.file_success2(file_name1, file_name2)
        else:
            self.file_failure2(file_name1, file_name2)

    def execute(self) -> int:
        self.logger.info("validator fresh dir:%s", self.fresh_dir)

        os.chdir(self.fresh_dir)
        targets = sorted(os.listdir("."))
        self.logger.info("%s files noted", len(targets))

        pairs, orphans = self._group_pairs(targets)
        self.logger.info(
            "%s pairs and %s invalid/orphan files noted", len(pairs), len(orphans)
        )

        for target1, target2 in pairs:
            self.file_processor(target1, target2)

        for orphan in orphans:
            self.file_failure(orphan)

        self.logger.info("validator success:%s failure:%s", self.success, self.failure)
        return 0


ValidatorEngine = HeelerValidator
Validator = HeelerValidator


# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
