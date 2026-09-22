#
# Title: json_helper.py
# Description: JSON schema support
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#

import json
import logging
import os

from jsonschema import validate

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("json_helper")

schema = {
    "type": "object",
    "properties": {
        "equipment": {
            "type": "object",
            "properties": {
                "hostName":     {"type": "string"},
                "hostType":     {"type": "string"},
            },
            "required": ["hostName", "hostType"],
            "additionalProperties": False
        },
        "geoLoc": {
            "type": "object",
            "properties": {
                "altitude":  {"type": "number"},
                "latitude":  {"type": "number"},
                "longitude": {"type": "number"},
                "siteName":  {"type": "string"},
            },
            "required": ["altitude", "latitude", "longitude", "siteName"],
            "additionalProperties": False
        },
        "job": {
            "type": "object",
            "properties": {
                "mode":    {"type": "string"},
                "project": {"type": "string"},
                "task":    {"type": "string"},
            },
            "required": ["mode", "project", "task"],
            "additionalProperties": False
        },
        "timeStamp": {
            "type": "object",
            "properties": {
                "epochSeconds": {"type": "number"},
                "iso8601":      {"type": "string"},
            },
            "required": ["epochSeconds", "iso8601"],
            "additionalProperties": False
        },
        "receiver": {
            "type": "object",
            "properties": {
                "antenna":    {"type": "string"},
                "receiverId": {"type": "number"},
                "task":       {"type": "string"},
                "type":       {"type": "string"},
            },
            "required": ["antenna", "receiverId", "task", "type"],
            "additionalProperties": False
        },
        "crateName":    {"type": "string"},
        "fileName":     {"type": "string"},
        "version":      {"type": "integer"},
        "observations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "bssid":         {"type": "string"},
                    "frequencyMhz":  {"type": "number"},
                    "signalDbm":     {"type": "number"},
                    "ssid":          {"type": "string"},
                    "capabilities":  {"type": "string"},
                    "cipherType":    {"type": "string"},
                },
                "required": ["bssid", "capabilities", "cipherType", "frequencyMhz", "signalDbm", "ssid"],
                "additionalProperties": False
            }
        },
    },
    "required": ["equipment", "geoLoc", "job", "receiver", "timeStamp", "crateName", "fileName", "version", "observations"],
    "additionalProperties": False
}

class JsonHelper:

    def __init__(self):
        self.raw_json = None

    def json_file_reader(self, file_name: str, validate_flag: bool) -> bool:
        try:
            with open(file_name, "r", encoding="utf-8") as in_file:
                self.raw_json = json.load(in_file)
        except Exception as error:
            logger.error(f"file read failed for {file_name}: {error}")
            return False

        if validate_flag:
            try:
                validate(instance=self.raw_json, schema=schema)
            except Exception as error:
                logger.error(f"json validation failed for {file_name}: {error}")
                return False

        return True

    def json_file_writer(self, file_name: str, json_data: dict[str, any]) -> bool:
        try:
            validate(instance=json_data, schema=schema)
        except Exception as error:
            logger.error(f"json validation failed for {file_name}: {error.message}")
            return False

        try:
            with open(file_name, "w") as out_file:
                json.dump(json_data, out_file, indent=4)
        except Exception as error:
            logger.error(f"file write failure for {file_name}: {error}")
            return False

        return True

    def _file_name_matches(self, payload_file_name: str, test_file_name: str) -> bool:
        if payload_file_name == test_file_name:
            return True

        return os.path.basename(payload_file_name) == os.path.basename(test_file_name)

    def json_file_tester(self, file_name: str, project: str, version: int) -> bool:
        if not os.path.isfile(file_name):
            logger.warning(f"skipping non-file:{file_name}")
            return False

        if os.path.getsize(file_name) < 1:
            logger.warning(f"skipping empty file:{file_name}")
            return False

        if not file_name.endswith(".json"):
            logger.warning(f"skipping non-json:{file_name}")
            return False

        if not self.json_file_reader(file_name, True):
            logger.warning(f"json file read/verify failure for {file_name}")
            return False

        if not self._file_name_matches(self.raw_json.get("fileName", ""), file_name):
            logger.warning(f"mismatched file name: {self.raw_json.get('fileName', 'missing')} vs {file_name}")
            return False

        if self.raw_json.get("version") != version:
            logger.warning(f"invalid version for {file_name}")
            return False

        payload_project = self.raw_json.get("job", {}).get("project")
        if payload_project != project:
            logger.warning(f"invalid project for {file_name}: {payload_project}")
            return False

        return True

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
