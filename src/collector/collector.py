#
# Title: collector.py
# Description: add a json header to iwlist scan output
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#

import datetime
import logging
import pydantic
import sys
import time
import uuid
import zoneinfo
from typing import Any

from parser import Parser

import yaml
from yaml.loader import SafeLoader

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("heeler")

class Equipment(pydantic.BaseModel):
    hostName: str
    hostType: str

class GeoLoc(pydantic.BaseModel):
    altitude: float
    latitude: float
    longitude: float
    siteName: str

class Job(pydantic.BaseModel):
    mode: str
    project: str
    task: str

class Observation(pydantic.BaseModel):
    bssid: str
    capabilities: str
    cipherType: str
    frequencyMhz: int
    signalDbm: int
    ssid: str

class Receiver(pydantic.BaseModel):
    antenna: str
    receiverId: int
    task: str
    type: str

class TimeStamp(pydantic.BaseModel):
    epochSeconds: int = pydantic.Field(default_factory=lambda: int(time.time()))
    iso8601: str = ""

    @pydantic.model_validator(mode="after")
    def sync_iso8601_from_epoch(self) -> "TimeStamp":
        self.iso8601 = datetime.datetime.fromtimestamp(
            self.epochSeconds, tz=zoneinfo.ZoneInfo("UTC")
        ).isoformat()
        return self

class HeelerModel(pydantic.BaseModel):
    crateName: str
    fileName: str
    version: int = 2
    equipment: Equipment
    geoLoc: GeoLoc
    job: Job
    receiver: Receiver
    timeStamp: TimeStamp
    observations: list[Observation]

class Collector:
    def __init__(self, args: dict[str, Any]):
        self.crate_name = args["crateName"]
        self.fresh_dir = args["freshDir"]
        self.gps_enable = args["gpsEnable"]

        self.equipment = Equipment(**args["equipment"])
        self.geo_loc = GeoLoc(**args["geoLoc"])
        self.receiver = Receiver(**args["receiver"])

        # heeler-v2-iwlist
        task = args["receiver"]["task"]
        tokens = task.split("-")
        mode = tokens[-1]
        project = "-".join(tokens[:-1])
        self.job = Job(mode=mode, project=project, task=task)

        self.time_stamp = TimeStamp()

    # copy the original iwlist file to fresh directory
    def copy_raw_file(self, source_file: str, dest_file: str) -> None:
        try:
            with open(source_file, "r") as in_file:
                with open(dest_file, "w") as out_file:
                    out_file.writelines(in_file.readlines())
        except Exception as error:
            logger.error(error)

    def execute(self, file_name: str) -> None:
        logger.info(f"collector reading: {file_name}")

        base_file_name = str(uuid.uuid4())
        logger.info(f"base filename: {base_file_name}")

        outfile_json = f"{self.fresh_dir}/{base_file_name}.json"
        outfile_raw = f"{self.fresh_dir}/{base_file_name}.raw"

        self.copy_raw_file(file_name, outfile_raw)

        parser = Parser()
        observations = parser.execute(file_name)

        obs_list = []
        for obs in observations:
            obs_list.append(Observation(**obs))

        time_stamp = TimeStamp()

        heeler_model = HeelerModel(
            crateName = self.crate_name,
            fileName = f"{base_file_name}.json",
            equipment=self.equipment,
            geoLoc=self.geo_loc,
            job=self.job,
            receiver=self.receiver,
            timeStamp=time_stamp,
            observations=obs_list,
        )

        with open(outfile_json, "w", encoding="utf-8") as out_file:
            out_file.write(heeler_model.model_dump_json(indent=4))

#
# argv[1] = configuration filename
#
if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_name = sys.argv[1]
    else:
        file_name = "config.yaml"

    with open(file_name, "r") as in_file:
        try:
            configuration = yaml.load(in_file, Loader=SafeLoader)
            collector = Collector(configuration)
            collector.execute(configuration["scanFile"])
        except yaml.YAMLError as error:
            print(error)

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
