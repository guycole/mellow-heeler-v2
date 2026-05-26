#
# Title: collector.py
# Description: add a json header to iwlist scan output
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#

import datetime
import json
import socket
import sys
import time
import uuid
import zoneinfo

from parser import Parser

import yaml
from yaml.loader import SafeLoader

class Collector:
    def __init__(self, args: dict[str, any]):
        self.crate_name = args["crateName"]
        self.fresh_dir = configuration["freshDir"]
        self.gps_enable = configuration["gpsEnable"]

        self.host_name = configuration['equipment']["hostName"]
        self.host_type = configuration['equipment']["type"]

        self.altitude = configuration["geoLoc"]["altitude"]
        self.latitude = configuration["geoLoc"]["latitude"]
        self.longitude = configuration["geoLoc"]["longitude"]
        self.site_name = configuration["geoLoc"]["siteName"]

        self.antenna = configuration["receiver"]["antenna"]
        self.receiver_id = configuration["receiver"]["receiver_id"]
        self.receiver_type = configuration["receiver"]["type"]

    def copy_raw_file(self, source_file: str, dest_file: str) -> None:
        try:
            with open(source_file, "r") as in_file:
                with open(dest_file, "w") as out_file:
                    out_file.writelines(in_file.readlines())
        except Exception as error:
            print(error)

    def json_file_writer(self, file_name: str, json_data: dict[str, any]) -> None:
        try:
            with open(file_name, "w") as out_file:
                json.dump(json_data, out_file, indent=4)
        except Exception as error:
            print(error)

    def execute(self, file_name: str) -> None:
        print(f"collector reading: {file_name}")

        base_file_name = str(uuid.uuid4())
        print(f"base filename: {base_file_name}")

        outfile_json = f"{self.fresh_dir}/{base_file_name}.json"
        outfile_raw = f"{self.fresh_dir}/{base_file_name}.raw"

        self.copy_raw_file(file_name, outfile_raw)

        parser = Parser()
        observations = parser.execute(file_name)

        epoch_seconds = int(time.time())
        dt_object_utc = datetime.datetime.fromtimestamp(
            epoch_seconds, tz=zoneinfo.ZoneInfo("UTC")
        )

        results = {
            "equipment": {
                "antenna": self.antenna,  
                "receiver_id": self.receiver_id,
                "receiver_type": self.receiver_type,
                "platform": self.host_type,
                "hostName": self.host_name  
            },
            "geoLoc": {
                "altitude": self.altitude,
                "latitude": self.latitude,
                "longitude": self.longitude,
                "siteName": self.site_name
            },
            "timeStamp": {
                "epochSeconds": epoch_seconds,
                "iso8601": dt_object_utc.isoformat()
            },
            "crate": self.crate_name,
            "fileName": f"{base_file_name}.json",
            "mode": "iwlist",
            "project": "heeler-v2",
            "version": 1,
            "observations": observations
        }

        self.json_file_writer(outfile_json, results)

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
