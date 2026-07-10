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
    host_name = Column(String)
    quantity_file = Column(Integer)
    quantity_obs = Column(Integer)
    score_date = Column(Date)

    def __init__(self, args: dict[str, any]):
        self.crate_name = args["crate_name"]
        self.file_quantity = args["file_quantity"]
        self.host_name = args["host_name"]
        self.obs_quantity = args["obs_quantity"]
        self.score_date = args["score_date"]

    def __repr__(self):
        return f"daily_score({self.score_date} {self.host_name})"

class LoadLog(Base):
    """load_log table definition"""

    __tablename__ = "heeler_load_log"

    id = Column(Integer, primary_key=True)
    crate_name = Column(String)
    epoch_seconds = Column(BigInteger)
    file_name = Column(String)
    file_type = Column(String)
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
        self.host_name = args["host_name"]
        self.load_time = args.get("load_time", datetime.now())
        self.obs_quantity = args["obs_quantity"]
        self.obs_time = args["obs_time"]
        self.site_name = args["site_name"]

    def __repr__(self):
        return f"load_log({self.file_name} {self.file_time} {self.file_type} {self.host_name})"

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
