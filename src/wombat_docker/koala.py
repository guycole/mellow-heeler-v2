#
# Title: koala.py
# Description: generate koala files
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
import logging
import datetime
import json
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("koala")

class Koala:

    def __init__(self):      
        # path from inside docker container
        self.koala_dir = "/mnt/wombat/heeler/koala"
        self.success_dir = "/mnt/wombat/heeler/success/"

        # path for local development
        # self.koala_dir = "/var/wombat/heeler/koala"
        # self.success_dir = "/var/wombat/heeler/success/"

        # UID/GID are provided by container entrypoint; default keeps local behavior.
        self.wombat_uid = int(os.getenv("WOMBAT_UID", "1000"))
        self.wombat_gid = int(os.getenv("WOMBAT_GID", "1000"))

    def file_reader(self, file_name: str) -> bool:
        try:
            with open(file_name, "r", encoding="utf-8") as in_file:
                self.raw_buffer = json.load(in_file)
        except Exception as error:
            logger.error(f"file read failed for {file_name}: {error}")
            return False

        return True
    
    def file_writer(self, file_name: str, content: dict) -> bool:
        try:
            with open(file_name, "w", encoding="utf-8") as out_file:
                json.dump(content, out_file)
        except Exception as error:
            logger.error(f"file write failed for {file_name}: {error}")
            return False

        return True

    def file_processor(self, file_name: str) -> dict[str, any]:
        if not self.file_reader(file_name):
            logger.warning(f"file read failed for {file_name}")
            return {}
        
        epochSeconds = self.raw_buffer.get("timeStamp", {}).get("epochSeconds", 0)
        
        result = {
            "epochSeconds": self.raw_buffer.get("timeStamp", {}).get("epochSeconds", 0),
            "geoLoc": {
                "site": self.raw_buffer.get("geoLoc", {}).get("siteName", "unknown")
            },
            "hostName": self.raw_buffer.get("equipment", {}).get("hostName", "unknown"),
            "project": self.raw_buffer.get("job", {}).get("project", "unknown"),
            "version": self.raw_buffer.get("version", 0),
            "wifi": self.raw_buffer.get("observations", []),
        }

        return result

    def execute(self) -> None:
        logger.info(f"success dir:{self.success_dir}")

        os.chdir(self.success_dir)
        targets = [ff for ff in os.listdir(".") if ff.endswith(".json")]
        logger.info(f"{len(targets)} files noted")

        # only process the most recent 
        candidates = {}
        max_list_size = 5
        for target in targets:
            candidate = self.file_processor(target)
            if len(candidate) > 0:
                key = f"{candidate['epochSeconds']}.{candidate['hostName']}"
                candidates[key] = candidate

        winner = None
        for key in sorted(candidates):
            winner = candidates[key]

        if winner is None:
            logger.warning("no valid candidates found")
            return

        out_file_name = f"{self.koala_dir}/{winner['epochSeconds']}.{winner['hostName']}"
        self.file_writer(out_file_name, winner)
        os.chown(out_file_name, self.wombat_uid, self.wombat_gid)

if __name__ == "__main__":
    koala = Koala()
    koala.execute()
    
# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
