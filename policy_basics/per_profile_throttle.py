import os
import json
import time
from datetime import datetime
from threading import Lock

import logging as log
from atakama import RulePlugin, ApprovalRequest, ProfileInfo

from policy_basics.simple_db import AbstractDb, FileDb, MemoryDb

LOCAL_TIMEZONE = datetime.now().astimezone().tzinfo

INFINITE = -1


class Timer:
    @staticmethod
    def now():
        return datetime.now(LOCAL_TIMEZONE)

    @staticmethod
    def time():
        return time.time()


class ProfileCount:
    hour_cnt: int = 0
    day_cnt: int = 0

    def __init__(self, timestamp=None, hour_cnt=0, day_cnt=0):
        if timestamp and (hour_cnt or day_cnt):
            now = Timer.now()
            reqtime = datetime.fromtimestamp(timestamp, LOCAL_TIMEZONE)

            reqdate = reqtime.date()
            today = now.date()
            if today != reqdate:
                day_cnt = 0

            reqhour = reqtime.hour
            curhour = now.hour
            if reqhour != curhour:
                hour_cnt = 0

        self._ts = int(timestamp or Timer.time())
        self.hour_cnt = int(hour_cnt)
        self.day_cnt = int(day_cnt)

    @staticmethod
    def from_dict(dat):
        return ProfileCount(dat["tm"], dat["hr"], dat["dy"])

    @staticmethod
    def from_str(dat: str):
        return ProfileCount.from_dict(json.loads(dat))

    def to_dict(self):
        return {"tm": self._ts, "hr": self.hour_cnt, "dy": self.day_cnt}

    def to_str(self) -> str:
        return self._dict_to_str(self.to_dict())

    @staticmethod
    def _dict_to_str(dct) -> str:
        return json.dumps(dct)


class ProfileThrottleDb:
    db: AbstractDb

    def __init__(self, args):
        self.__lock = Lock()
        if not args.get("persistent", False):
            self.db = MemoryDb()
        else:
            path = str(args.get("db-file", os.path.expanduser("~/profile-throttle.db")))
            try:
                self.db = FileDb(path)
            except Exception as ex:  # pylint: disable=broad-except
                # deal with corruption by recovering
                log.error("unable to open %s: %s", path, repr(ex))
                # save the old one, maybe for debugging or something
                os.replace(path, path + ".old")
                self.db = FileDb(path)

    @staticmethod
    def _bytes_to_str(byt):
        return byt.hex()

    def get(self, profile_id: bytes) -> ProfileCount:
        data = self.db.get(self._bytes_to_str(profile_id))
        if not data:
            return ProfileCount()
        try:
            return ProfileCount.from_str(data)
        except (ValueError, TypeError, AssertionError, KeyError):
            log.warning("invalid value in db, resetting: (%s)", data)
            return ProfileCount()

    def increment(self, profile_id: bytes):
        with self.__lock:
            pc = self.get(profile_id)
            pc.hour_cnt += 1
            pc.day_cnt += 1
            self.db.set(self._bytes_to_str(profile_id), pc.to_str())
        return pc

    def clear(self, profile_id: bytes):
        self.db.remove(self._bytes_to_str(profile_id))


class ProfileThrottleRule(RulePlugin):
    """
    Basic rule for per-profile limits:

    YML Arguments:
     - per_hour: reqyests per hour
     - per_day: reqyests per day
     - persistent: restarting the server not clear current quotas

    ```
    Example:
        - rule: per-profile-throttle-rule
          per_hour: 10
          per_day: 100
          persistent: False
    ```
    """

    @staticmethod
    def name() -> str:
        return "per-profile-throttle-rule"

    def __init__(self, args):
        super().__init__(args)
        self.per_hour = args.get("per_hour", INFINITE)
        self.per_day = args.get("per_day", INFINITE)
        self.db = ProfileThrottleDb(args)

    def approve_request(self, request: ApprovalRequest):
        return self._approve_profile_request(request.profile.profile_id)

    def _approve_profile_request(self, profile_id):
        pc = self.db.increment(profile_id)
        return (self.per_day == INFINITE or pc.day_cnt <= self.per_day) and (
            self.per_hour == INFINITE or pc.hour_cnt <= self.per_hour
        )

    def clear_quota(self, profile: ProfileInfo) -> None:
        self.db.clear(profile.profile_id)
