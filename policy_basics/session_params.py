# SPDX-FileCopyrightText: © Atakama, Inc <support@atakama.com>
# SPDX-License-Identifier: LGPL-3.0-or-later

from collections import defaultdict
from typing import Optional, Dict, List, Tuple, Set

from atakama import RulePlugin, ApprovalRequest

from policy_basics.time_range import TimeArgs

MINIMUM_WORD_COUNT = 4


class SessionParamsRule(RulePlugin):
    """
    Container rule for session parameters.

    YML Arguments:
     - max_request_count: int
     - max_time_seconds: int
     - end_by_time: HH:MM[am|pm] [TZ]
    ```
    Example:
        - rule: session-params-rule
        - max_request_count: 100
        - max_time_seconds: 28800
        - end_by_time: 5:00pm EST
    ```
    ```
    """

    NO_MAXIMUM = 0
    DEFAULT_MAX_TIME = 300  # 5 minute session default
    MAX_VALID_TIME = 86400 * 7  # one-week session is too long
    MIN_VALID_TIME = 1  # 1-second session is too short

    @staticmethod
    def name() -> str:
        return "session-params-rule"

    def __init__(self, args):
        self.max_request_count = args.get("max_request_count", self.NO_MAXIMUM)
        assert self.max_request_count > 0 or self.max_request_count == self.NO_MAXIMUM, "invalid request count"
        self.max_time_seconds = args.get("max_time_seconds", self.DEFAULT_MAX_TIME)
        assert self.max_time_seconds < self.MAX_VALID_TIME, "invalid maximum session time"
        assert self.max_time_seconds > self.MIN_VALID_TIME, "invalid minimum session time"
        end_by_time = args.get("end_by_time", None)
        if end_by_time:
            self.end_by_time = TimeArgs.str_to_time(end_by_time)
        super().__init__(args)

    def approve_request(self, request: ApprovalRequest) -> Optional[bool]:
        return True
