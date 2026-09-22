#
# Title: sql_table.py
# Description: database table definitions
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import BigInteger, Boolean, Date, DateTime, Float, Integer, SmallInteger, String

from sqlalchemy.orm import registry
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.declarative import declared_attr

mapper_registry = registry()

def _arg(args: dict[str, any], camel_key: str, snake_key: str | None = None):
    if camel_key in args:
        return args[camel_key]

    if snake_key is not None and snake_key in args:
        return args[snake_key]

    raise KeyError(camel_key)

class Base(DeclarativeBase):
    pass

class BssidScore(Base):
    __tablename__ = "heeler_bssid_score"

    id = Column(BigInteger, primary_key=True)
    bssid = Column(String)
    quantity = Column(Integer)

    def __init__(self, args: dict[str, any]):
        self.bssid = args["bssid"]
        self.quantity = args["quantity"]

    def __repr__(self):
        return f"bssid_score({self.bssid} {self.quantity})"

class DailyScore(Base):
    __tablename__ = "heeler_daily_score"

    id = Column(BigInteger, primary_key=True)
    crate_name = Column(String)
    file_quantity = Column(Integer)
    host_name = Column(String)
    obs_quantity = Column(Integer)
    score_date = Column(Date)

    def __init__(self, args: dict[str, any]):
        self.crate_name = _arg(args, "crateName", "crate_name")
        self.file_quantity = _arg(args, "fileQuantity", "file_quantity")
        self.host_name = _arg(args, "hostName", "host_name")
        self.obs_quantity = _arg(args, "obsQuantity", "obs_quantity")
        self.score_date = _arg(args, "scoreDate", "score_date")

    def __repr__(self):
        return f"daily_score({self.score_date} {self.host_name})"

class GeoLoc(Base):
    __tablename__ = "heeler_geo_loc"

    id = Column(BigInteger, primary_key=True)
    altitude = Column(Float)
    course = Column(Float)
    fix_time = Column(DateTime)
    host_name = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    site_name = Column(String)
    speed = Column(Float)
   
    def __init__(self, args: dict[str, any]):
        self.altitude = _arg(args, "altitude")
        self.course = _arg(args, "course")
        self.fix_time = _arg(args, "fixTime", "fix_time")
        self.host_name = _arg(args, "hostName", "host_name")
        self.latitude = _arg(args, "latitude")
        self.longitude = _arg(args, "longitude")
        self.site_name = _arg(args, "siteName", "site_name")
        self.speed = _arg(args, "speed")

    def __repr__(self):
        return f"geo_loc({self.site_name} {self.host_name})"

class LoadLog(Base):
    __tablename__ = "heeler_load_log"

    id = Column(BigInteger, primary_key=True)
    crate_name = Column(String)
    epoch_seconds = Column(BigInteger)
    file_name = Column(String)
    geo_loc_id = Column(BigInteger)
    host_name = Column(String)
    load_time = Column(DateTime)
    mode = Column(String)
    obs_quantity = Column(SmallInteger)
    obs_time = Column(DateTime)
    site_name = Column(String)
    task = Column(String)

    def __init__(self, args: dict[str, any]):
        self.crate_name = _arg(args, "crateName", "crate_name")
        self.epoch_seconds = _arg(args, "epochSeconds", "epoch_seconds")
        self.file_name = _arg(args, "fileName", "file_name")
        self.geo_loc_id = _arg(args, "geoLocId", "geo_loc_id")
        self.host_name = _arg(args, "hostName", "host_name")
        self.load_time = args.get("loadTime", args.get("load_time", datetime.now()))
        self.mode = _arg(args, "mode")
        self.obs_quantity = _arg(args, "obsQuantity", "obs_quantity")
        self.obs_time = _arg(args, "obsTime", "obs_time")
        self.site_name = _arg(args, "siteName", "site_name")
        self.task = _arg(args, "task")

    def __repr__(self):
        return f"load_log({self.file_name} {self.obs_time} {self.task} {self.host_name})"

class Observation(Base):
    """observation table definition"""

    __tablename__ = "heeler_observation"

    id = Column(BigInteger, primary_key=True)
    bssid = Column(String)
    load_log_id = Column(BigInteger)
    obs_time = Column(DateTime)
    signal_dbm = Column(SmallInteger)
    wap_id = Column(BigInteger)

    def __init__(self, args: dict[str, any]):
        self.bssid = _arg(args, "bssid")
        self.load_log_id = _arg(args, "loadLogId", "load_log_id")
        self.obs_time = _arg(args, "obsTime", "obs_time")
        self.signal_dbm = _arg(args, "signalDbm", "signal_dbm")
        self.wap_id = _arg(args, "wapId", "wap_id")

    def __repr__(self):
        return f"observation({self.wap_id} {self.load_log_id} {self.bssid})"

class Wap(Base):
    """wap table definition"""

    __tablename__ = "heeler_wap"

    id = Column(BigInteger, primary_key=True)
    bssid = Column(String)
    capability = Column(String)
    cipher = Column(String)
    frequency_mhz = Column(SmallInteger)
    ssid = Column(String)
    version = Column(Integer)

    def __init__(self, args: dict[str, any]):
        self.bssid = _arg(args, "bssid")
        self.capability = _arg(args, "capability")
        self.cipher = _arg(args, "cipher")
        self.frequency_mhz = _arg(args, "frequencyMhz", "frequency_mhz")
        self.ssid = _arg(args, "ssid")
        self.version = _arg(args, "version")

    def __repr__(self):
        return f"wap({self.bssid} {self.version} {self.ssid})"

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
