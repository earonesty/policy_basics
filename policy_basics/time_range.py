from typing import Optional, List
from datetime import date, time, datetime

import dateutil.parser
from atakama import RulePlugin, ApprovalRequest

LOCAL_TIMEZONE = datetime.now().astimezone().tzinfo


class TimeArgs:
    # see https://docs.python.org/3/library/datetime.html#datetime.date.weekday
    ALL_DAYS: List[int] = [0, 1, 2, 3, 4, 5, 6]

    def __init__(  # pylint: disable=too-many-arguments
        self,
        days: List[int],
        include: List[date],
        exclude: List[date],
        time_start: Optional[time] = None,
        time_end: Optional[time] = None,
    ):
        self.days_of_week = days
        self.include = include
        self.exclude = exclude
        self.time_of_day_start = time_start
        self.time_of_day_end = time_end
        assert all(0 <= d <= 6 for d in self.days_of_week), "invalid day of week"

    def in_range(self, now: datetime):
        if now.date() in self.exclude:
            return False

        if now.date() not in self.include and now.weekday() not in self.days_of_week:
            return False

        if not (self.time_of_day_start and self.time_of_day_end):
            return True

        return self.time_of_day_start <= now.timetz() <= self.time_of_day_end

    @classmethod
    def from_dict(cls, args):
        return TimeArgs(
            days=args.get("days", cls.ALL_DAYS),
            include=cls.strs_to_dates(args.get("include", [])),
            exclude=cls.strs_to_dates(args.get("exclude", [])),
            time_start=cls.strs_to_time(args.get("time_start", None)),
            time_end=cls.strs_to_time(args.get("time_end", None)),
        )

    @staticmethod
    def strs_to_dates(strs: List[str]):
        assert isinstance(strs, list), "input must be a list"
        return [dateutil.parser.parse(s).date() for s in strs]

    @staticmethod
    def strs_to_time(tim: Optional[str]):
        if not tim:
            return None
        timetz = dateutil.parser.parse(tim).timetz()
        if not timetz.tzinfo:
            timetz = timetz.replace(tzinfo=LOCAL_TIMEZONE)
        return timetz


class TimeRangeRule(RulePlugin):
    """
    Basic rule for time ranges:

    YML Arguments:
     - time_start: time start (hh:mm)
     - time_end: time end (hh:mm)
     - days: list of days of the week, monday=0, default is 0-6
     - include: list of specific dates to include
     - exclude: list of specific dates to exclude

    ```
    Example:
        - rule: time-range-policy
          time_start: 9:00am
          time_end: 5:00pm
          exclude: 2022-06-01
    ```
    """

    @staticmethod
    def name() -> str:
        return "time-range-policy"

    def __init__(self, args):
        super().__init__(args)
        self.times = TimeArgs.from_dict(args)

    def approve_request(self, request: ApprovalRequest) -> Optional[bool]:
        now = datetime.now()
        return self.times.in_range(now)
