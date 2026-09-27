#
# Title: postgres.py
# Description: postgresql support
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
# import sqlalchemy
# from sqlalchemy import and_
# from sqlalchemy import select

import datetime
import logging
from typing import Any

import sqlalchemy
from sqlalchemy import and_
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy import select

from .sql_table import (
    BssidScore,
    DailyScore,
    GeoLoc,
    LoadLog,
    Observation,
    Wap,
)


logger = logging.getLogger("postgres")


class PostGres:
    def __init__(
        self,
        session: sqlalchemy.orm.session.sessionmaker,
        logger_instance: logging.Logger | None = None,
    ):
        self.Session = session
        self.logger = logger_instance or logger

    def bssid_score_insert_or_update(self, args: dict[str, Any]) -> BssidScore:
        candidate = BssidScore(args)

        try:
            with self.Session() as session:
                existing = session.scalars(
                    select(BssidScore).filter(
                        and_(BssidScore.bssid == candidate.bssid,)
                    )
                ).first()

                if existing is None:
                    session.add(candidate)
                else:
                    existing.quantity += candidate.quantity

                session.commit()
        except Exception as error:
            self.logger.error("bssid score update failed: %s", error)

        return candidate

    def daily_score_insert_or_update(self, args: dict[str, Any]) -> DailyScore:
        candidate = DailyScore(args)

        try:
            with self.Session() as session:
                existing = session.scalars(
                    select(DailyScore).filter(
                        and_(
                            DailyScore.score_date == candidate.score_date,
                            DailyScore.host_name == candidate.host_name,
                        )
                    )
                ).first()

                if existing is None:
                    session.add(candidate)
                else:
                    existing.file_quantity += candidate.file_quantity
                    existing.obs_quantity += candidate.obs_quantity

                session.commit()
        except Exception as error:
            self.logger.error("daily score update failed: %s", error)

        return candidate

    def geo_loc_select_by_site(self, site_name: str) -> list[GeoLoc]:
        statement = select(GeoLoc).filter_by(site_name=site_name).order_by(GeoLoc.fix_time)

        with self.Session() as session:
            return session.scalars(statement).all()

    def load_log_insert(self, args: dict[str, Any]) -> LoadLog:
        candidate = LoadLog(args)

        try:
            with self.Session() as session:
                session.add(candidate)
                session.commit()
        except Exception as error:
            self.logger.error("load log insert failed: %s", error)

        return candidate

    def load_log_select_all(self) -> list[LoadLog]:
        with self.Session() as session:
            return session.scalars(
                select(LoadLog).order_by(desc(LoadLog.load_time), desc(LoadLog.id))
            ).all()

    def load_log_select_all_by_date(self, target: datetime.date) -> list[LoadLog]:
        with self.Session() as session:
            return session.scalars(
                select(LoadLog)
                .filter(func.date(LoadLog.load_time) == target)
                .order_by(desc(LoadLog.load_time), desc(LoadLog.id))
            ).all()

    def load_log_select_by_file_name(self, file_name: str) -> LoadLog:
        with self.Session() as session:
            return session.scalars(
                select(LoadLog).filter_by(file_name=file_name)
            ).first()

    def observation_insert(self, args: dict[str, Any]) -> Observation:
        candidate = Observation(args)

        try:
            with self.Session() as session:
                session.add(candidate)
                session.commit()
        except Exception as error:
            self.logger.error("observation insert failed: %s", error)

        return candidate

    def wap_insert(self, args: dict[str, Any]) -> Wap:
        candidate = Wap(args)

        try:
            with self.Session() as session:
                session.add(candidate)
                session.commit()
        except Exception as error:
            self.logger.error("wap insert failed: %s", error)

        return candidate

    def wap_select(self, wap: dict[str, Any]) -> list[Wap]:
        statement = select(Wap).filter(
            and_(
                Wap.bssid == wap["bssid"].lower(),
                Wap.ssid == wap["ssid"],
                Wap.capability == wap["capability"],
                Wap.cipher == wap["cipher"],
                Wap.frequency_mhz == wap["frequency_mhz"],
            )
        ).order_by(Wap.version)

        with self.Session() as session:
            return session.scalars(statement).all()

    def wap_select_by_bssid(self, bssid: str) -> list[Wap]:
        statement = select(Wap).filter_by(bssid=bssid.lower()).order_by(Wap.version)

        with self.Session() as session:
            return session.scalars(statement).all()

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
