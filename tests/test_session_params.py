# SPDX-FileCopyrightText: © Atakama, Inc <support@atakama.com>
# SPDX-License-Identifier: LGPL-3.0-or-later

# pylint: disable=invalid-name
import dateutil.parser
import pytest

from policy_basics.session_params import SessionParamsRule


def test_session_params():
    tr = SessionParamsRule(
        {
            "max_request_count": 100,
            "max_time_seconds": 100,
            "end_by_time": "5:00pm+04:00",
        }
    )
    assert tr.end_by_time
    assert tr.max_request_count == 100
    assert tr.max_time_seconds == 100

    tr = SessionParamsRule(
        {
        }
    )
    assert tr.max_request_count == tr.NO_MAXIMUM
    assert tr.max_time_seconds == tr.DEFAULT_MAX_TIME
    assert not tr.end_by_time


def test_session_valid():
    with pytest.raises(dateutil.parser.ParserError):
        SessionParamsRule(
            {
                "end_by_time": "bad",
            }
        )

    with pytest.raises(AssertionError):
        SessionParamsRule(
            {
                "max_request_count": -1,
            }
        )

    with pytest.raises(AssertionError):
        SessionParamsRule(
            {
                "max_time_seconds": 100000000000000,
                "rule_id": 55,
            }
        )
