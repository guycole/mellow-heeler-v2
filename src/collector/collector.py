#
# Title: collector.py
# Description: add a json header to iwlist scan output
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#

import datetime
import logging
import sys
import time
import uuid
import zoneinfo
from abc import ABC, abstractmethod
from typing import Any

import pydantic
import yaml
from parser import Parser
from yaml.loader import SafeLoader

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("heeler")


class Equipment(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(populate_by_name=True)

    host_name: str = pydantic.Field(alias="hostName")
    host_type: str = pydantic.Field(alias="hostType")


class GeoLoc(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(populate_by_name=True)

    altitude: float
    latitude: float
    longitude: float
    site_name: str = pydantic.Field(alias="siteName")


class Job(pydantic.BaseModel):
    mode: str
    project: str
    task: str


class Observation(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(populate_by_name=True)

    bssid: str
    capabilities: str
    cipher_type: str = pydantic.Field(alias="cipherType")
    frequency_mhz: int = pydantic.Field(alias="frequencyMhz")
    signal_dbm: int = pydantic.Field(alias="signalDbm")
    ssid: str


class Receiver(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(populate_by_name=True)

    antenna: str
    receiver_id: int = pydantic.Field(alias="receiverId")
    task: str
    type: str


class TimeStamp(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(populate_by_name=True)

    epoch_seconds: int = pydantic.Field(
        default_factory=lambda: int(time.time()), alias="epochSeconds"
    )
    iso8601: str = ""

    @pydantic.model_validator(mode="after")
    def sync_iso8601_from_epoch(self) -> "TimeStamp":
        self.iso8601 = datetime.datetime.fromtimestamp(
            self.epoch_seconds, tz=zoneinfo.ZoneInfo("UTC")
        ).isoformat()
        return self


class HeelerModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(populate_by_name=True)

    crate_name: str = pydantic.Field(alias="crateName")
    file_name: str = pydantic.Field(alias="fileName")
    version: int = 2
    equipment: Equipment
    geo_loc: GeoLoc = pydantic.Field(alias="geoLoc")
    job: Job
    receiver: Receiver
    time_stamp: TimeStamp = pydantic.Field(alias="timeStamp")
    observations: list[Observation]


class Collector(ABC):
    @abstractmethod
    def get_observations(self, file_name: str) -> list[Observation]:
        pass

    @abstractmethod
    def execute(self, file_name: str) -> int:
        pass


class HeelerCollector(Collector):
    def __init__(self, args: dict[str, Any]):
        self.crate_name = args["crateName"]
        self.fresh_dir = args["freshDir"]
        self.gps_enable = args["gpsEnable"]

        self.equipment = Equipment(**args["equipment"])
        self.geo_loc = GeoLoc(**args["geoLoc"])
        self.receiver = Receiver(**args["receiver"])
        self.time_stamp = TimeStamp()

        # heeler-v2-iwlist
        task = args["receiver"]["task"]
        tokens = task.split("-")
        mode = tokens[-1]
        project = "-".join(tokens[:-1])
        self.job = Job(mode=mode, project=project, task=task)

    def copy_raw_file(self, source_file: str, dest_file: str) -> None:
        try:
            with open(source_file, "r", encoding="utf-8") as in_file:
                with open(dest_file, "w", encoding="utf-8") as out_file:
                    out_file.writelines(in_file.readlines())
        except OSError as error:
            logger.error("copy raw file failed: %s", error)

    def get_observations(self, file_name: str) -> list[Observation]:
        parser = Parser()
        parsed = parser.execute(file_name)
        return [Observation(**obs) for obs in parsed]

    def execute(self, file_name: str) -> int:
        logger.info("collector reading: %s", file_name)

        base_file_name = str(uuid.uuid4())
        logger.info("base filename: %s", base_file_name)

        outfile_json = f"{self.fresh_dir}/{base_file_name}.json"
        outfile_raw = f"{self.fresh_dir}/{base_file_name}.raw"

        self.copy_raw_file(file_name, outfile_raw)
        observations = self.get_observations(file_name)

        heeler_model = HeelerModel(
            crate_name=self.crate_name,
            file_name=f"{base_file_name}.json",
            equipment=self.equipment,
            geo_loc=self.geo_loc,
            job=self.job,
            receiver=self.receiver,
            time_stamp=self.time_stamp,
            observations=observations,
        )

        with open(outfile_json, "w", encoding="utf-8") as out_file:
            out_file.write(heeler_model.model_dump_json(indent=4, by_alias=True))

        return 0


#
# argv[1] = configuration filename
#
if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_name = sys.argv[1]
    else:
        file_name = "config.yaml"

    with open(file_name, "r", encoding="utf-8") as in_file:
        try:
            configuration = yaml.load(in_file, Loader=SafeLoader)
            collector = HeelerCollector(configuration)
            exit(collector.execute(configuration["scanFile"]))
        except yaml.YAMLError as error:
            logger.error("YAML parse error: %s", error)

    exit(1)

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
