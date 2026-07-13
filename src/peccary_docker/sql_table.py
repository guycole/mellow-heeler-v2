#
# Title: sql_table.py
# Description: database table definitions
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import BigInteger, Boolean, Date, DateTime, Float, Integer, String

from sqlalchemy.orm import registry
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.declarative import declared_attr

mapper_registry = registry()

class Base(DeclarativeBase):
    pass

class DailyScore(Base):
    __tablename__ = "heeler_daily_score"

    id = Column(Integer, primary_key=True)
    crate_name = Column(String)
    file_quantity = Column(Integer)
    host_name = Column(String)
    obs_quantity = Column(Integer)
    score_date = Column(Date)

    def __init__(self, args: dict[str, any]):
        self.crate_name = args["crate_name"]
        self.file_quantity = args["file_quantity"]
        self.host_name = args["host_name"]
        self.obs_quantity = args["obs_quantity"]
        self.score_date = args["score_date"]

    def __repr__(self):
        return f"daily_score({self.score_date} {self.host_name})"

class GeoLoc(Base):
    __tablename__ = "heeler_geo_loc"

    id = Column(Integer, primary_key=True)
    altitude = Column(Float)
    course = Column(Float)
    fix_time = Column(DateTime)
    host_name = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    site_name = Column(String)
    speed = Column(Float)
   
    def __init__(self, args: dict[str, any]):
        self.altitude = args["altitude"]
        self.course = args["course"]
        self.fix_time = args["fix_time"]
        self.host_name = args["host_name"]
        self.latitude = args["latitude"]
        self.longitude = args["longitude"]
        self.site_name = args["site_name"]
        self.speed = args["speed"]

    def __repr__(self):
        return f"geo_loc({self.site_name} {self.host_name})"

class LoadLog(Base):
    __tablename__ = "heeler_load_log"

    id = Column(Integer, primary_key=True)
    crate_name = Column(String)
    epoch_seconds = Column(BigInteger)
    file_name = Column(String)
    file_type = Column(String)
    geo_loc_id = Column(BigInteger)
    host_name = Column(String)
    load_time = Column(DateTime)
    obs_quantity = Column(Integer)
    obs_time = Column(DateTime)
    site_name = Column(String)

    def __init__(self, args: dict[str, any]):
        self.crate_name = args["crate_name"]
        self.epoch_seconds = args["epoch_seconds"]
        self.file_name = args["file_name"]
        self.file_type = args["file_type"]
        self.geo_loc_id = args["geo_loc_id"]
        self.host_name = args["host_name"]
        self.load_time = args.get("load_time", datetime.now())
        self.obs_quantity = args["obs_quantity"]
        self.obs_time = args["obs_time"]
        self.site_name = args["site_name"]

    def __repr__(self):
        return f"load_log({self.obs_time} {self.file_type} {self.host_name} {self.file_name})"

class Observation(Base):
    """observation table definition"""

    __tablename__ = "heeler_observation"

    id = Column(Integer, primary_key=True)
    bssid = Column(String)
    load_log_id = Column(BigInteger)
    obs_time = Column(DateTime)
    signal_dbm = Column(Integer)
    wap_id = Column(BigInteger)

    def __init__(self, args: dict[str, any]):
        self.bssid = args["bssid"]
        self.load_log_id = args["load_log_id"]
        self.obs_time = args["obs_time"]
        self.signal_dbm = args["signal_dbm"]
        self.wap_id = args["wap_id"]

    def __repr__(self):
        return f"observation({self.wap_id} {self.load_log_id} {self.bssid})"

class Wap(Base):
    """wap table definition"""

    __tablename__ = "heeler_wap"

    id = Column(Integer, primary_key=True)
    bssid = Column(String)
    capability = Column(String)
    cipher = Column(String)
    frequency_mhz = Column(Integer)
    ssid = Column(String)
    version = Column(Integer)

    def __init__(self, args: dict[str, any]):
        self.bssid = args["bssid"]
        self.capability = args["capability"]
        self.cipher = args["cipher"]
        self.frequency_mhz = args["frequency_mhz"]
        self.ssid = args["ssid"]
        self.version = args["version"]

    def __repr__(self):
        return f"wap({self.bssid} {self.version} {self.ssid})"

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
