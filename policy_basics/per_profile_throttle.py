# SPDX-FileCopyrightText: © Atakama, Inc <support@atakama.com>
# SPDX-License-Identifier: LGPL-3.0-or-later

import os
import json
import time
from datetime import datetime

import logging
from typing import Optional, Union

from atakama import RulePlugin, ApprovalRequest, ProfileInfo

from policy_basics.simple_db import UriDb, MemoryDb

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

LOCAL_TIMEZONE = datetime.now().astimezone().tzinfo

INFINITE = -1
# A mofnop times out in 60 seconds. Allow 30 seconds of clock skew. => 90 second default
DEFAULT_EXPIRY_TIME = 90


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

    def __init__(
        self,
        timestamp=None,
        hour_cnt=0,
        day_cnt=0,
        lock_value: Optional[str] = None,
        expiry_secs: float = DEFAULT_EXPIRY_TIME,
    ):
        # pylint: disable=too-many-arguments
        if timestamp and (hour_cnt or day_cnt):
            now = Timer.now()
            reqtime = datetime.fromtimestamp(timestamp, LOCAL_TIMEZONE)

            reqdate = reqtime.date()
            today = now.date()
            if today != reqdate:
                day_cnt = 0
                hour_cnt = 0
            else:
                reqhour = reqtime.hour
                curhour = now.hour
                if reqhour != curhour:
                    hour_cnt = 0

        self._ts = Timer.time()
        self.hour_cnt = int(hour_cnt)
        self.day_cnt = int(day_cnt)
        if timestamp and timestamp + expiry_secs < self._ts:
            self.lock_value = None
        else:
            self.lock_value = lock_value

    @staticmethod
    def from_dict(dat, expiry_secs=DEFAULT_EXPIRY_TIME):
        return ProfileCount(
            dat["tm"],
            dat["hr"],
            dat["dy"],
            dat.get("lk", None),
            expiry_secs=expiry_secs,
        )

    @staticmethod
    def from_str(dat: str, expiry_secs=DEFAULT_EXPIRY_TIME):
        return ProfileCount.from_dict(json.loads(dat), expiry_secs=expiry_secs)

    def to_dict(self, lock_value: str = None):
        ret = {"tm": self._ts, "hr": self.hour_cnt, "dy": self.day_cnt}
        if lock_value is not None:
            ret["lk"] = lock_value
        return ret

    def to_str(self, lock_value: str = None) -> str:
        return self._dict_to_str(self.to_dict(lock_value))

    @staticmethod
    def _dict_to_str(dct) -> str:
        return json.dumps(dct)

    def increment(self):
        self.hour_cnt += 1
        self.day_cnt += 1


class ProfileThrottleDb:
    db: Union[MemoryDb, UriDb]

    def __init__(self, args):
        self.lock_value = os.urandom(8).hex()
        self.expiry_secs = args.get("expiry_secs", DEFAULT_EXPIRY_TIME)
        if not args.get("persistent", False):
            self.db = MemoryDb()
        else:
            uri = args.get("db-uri")
            kws = {}
            if args.get("db-table"):
                kws["table"] = args.get("db-table")
            path = (
                str(args.get("db-file", os.path.expanduser("~/profile-throttle.db")))
                if not uri
                else None
            )
            try:
                self.db = UriDb(path=path, uri=uri, **kws)
            except Exception as ex:  # pylint: disable=broad-except
                if path:
                    # deal with corruption by recovering
                    log.error("unable to open %s: %s", path, repr(ex))
                    # save the old one, maybe for debugging or something
                    os.replace(path, path + ".old")
                    self.db = UriDb(path)
                else:
                    raise

    @staticmethod
    def _get_db_key(rule_id: str, profile_id: bytes):
        return profile_id.hex() + ":" + rule_id

    def get(
        self, rule_id: str, profile_id: bytes, lock: bool
    ) -> Optional[ProfileCount]:
        """Gets the row in the db.

        Args:
            lock - Whether or not to try to lock the row

        Returns None if the row is already locked by someone else, otherwise a ProfileCount object.
        """
        key = self._get_db_key(rule_id, profile_id)
        data = self.db.get(key)
        pc = None
        if not data:
            pc = ProfileCount()
            if lock:
                self.db.set(key, pc.to_str(self.lock_value))
            return pc
        try:
            pc = ProfileCount.from_str(data, expiry_secs=self.expiry_secs)
        except (ValueError, TypeError, AssertionError, KeyError):
            log.warning("invalid value in db, resetting: (%s)", data)
            pc = ProfileCount()
            if lock:
                self.db.set(key, pc.to_str(self.lock_value))
            return pc
        if lock:
            if self.is_locked(pc):
                return None
            self.db.set(key, pc.to_str(self.lock_value))
            return pc
        return pc

    def increment(self, rule_id: str, profile_id: bytes, pc: ProfileCount):
        pc.increment()
        self.db.set(self._get_db_key(rule_id, profile_id), pc.to_str(lock_value=None))
        return pc

    def lock(self, rule_id, profile_id, pc: ProfileCount):
        self.db.set(
            self._get_db_key(rule_id, profile_id), pc.to_str(lock_value=self.lock_value)
        )

    def unlock(self, rule_id, profile_id, pc: ProfileCount):
        self.db.set(self._get_db_key(rule_id, profile_id), pc.to_str(lock_value=None))

    def is_locked(self, pc):
        """Returns whether or not the row is locked by someone else."""
        return not ((pc.lock_value is None) or (pc.lock_value == self.lock_value))

    def clear(self, rule_id: str, profile_id: bytes):
        self.db.remove(self._get_db_key(rule_id, profile_id))


class ProfileThrottleRule(RulePlugin):
    """
    Basic rule for per-profile limits:

    YML Arguments:
     - per_hour: requests per hour
     - per_day: requests per day
     - persistent: restarting the server not clear current quotas

    ```
    Example:
        - rule: per-profile-throttle-rule
          per_hour: 10
          per_day: 100
          persistent: False
    ```

    Request data are stored per-rule. If there are 2 throttle rules which may match a profile,
    each will record its own request counts for that profile, i.e. the limits are additive.
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
        if (pc := self.db.get(self.rule_id, profile_id, lock=True)) is None:
            log.warning(
                "ProfileThrottleRule._approve_profile_request rule_id=%s is_locked=True",
                self.rule_id,
            )
            return False
        within = self._within_quota(pc)
        if not within:
            self.db.unlock(self.rule_id, profile_id, pc)
        log.debug(
            "ProfileThrottleRule._approve_profile_request rule_id=%s within=%s "
            "day_cnt=%i hour_cnt=%i",
            self.rule_id,
            within,
            pc.day_cnt,
            pc.hour_cnt,
        )
        return within

    def use_quota(self, request: ApprovalRequest):
        return self._use_quota(request.profile.profile_id)

    def _use_quota(self, profile_id):
        if (pc := self.db.get(self.rule_id, profile_id, lock=True)) is None:
            log.warning(
                "ProfileThrottleRule._approve_profile_request rule_id=%s is_locked=True",
                self.rule_id,
            )
            # There should be a more descriptive error in atakama_sdk that we can use here.
            raise RuntimeError("Profile Row is being handled by another process")
        pc = self.db.increment(self.rule_id, profile_id, pc)
        log.debug(
            "ProfileThrottleRule._use_quota rule_id=%s now day_cnt=%i hour_cnt=%i",
            self.rule_id,
            pc.day_cnt,
            pc.hour_cnt,
        )

    def _approve_and_use_quota(self, profile_id):
        # For tests
        if self._approve_profile_request(profile_id):
            self._use_quota(profile_id)
            return True
        return False

    def _within_quota(self, pc):
        return (self.per_day == INFINITE or pc.day_cnt < self.per_day) and (
            self.per_hour == INFINITE or pc.hour_cnt < self.per_hour
        )

    def clear_quota(self, profile: ProfileInfo) -> None:
        self.db.clear(self.rule_id, profile.profile_id)

    def at_quota(self, profile: ProfileInfo) -> bool:
        pc = self.db.get(self.rule_id, profile.profile_id, lock=False)
        return not self._within_quota(pc)
