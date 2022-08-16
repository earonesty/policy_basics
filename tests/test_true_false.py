# SPDX-FileCopyrightText: © Atakama, Inc <support@atakama.com>
# SPDX-License-Identifier: LGPL-3.0-or-later

from atakama import ApprovalRequest

from policy_basics.true_false import ApproveRule, RejectRule


def test_true():
    approval = ApproveRule({"rule_id": "void pointer"})
    assert approval.approve_request(None)
    assert approval.approve_request(True)
    assert approval.approve_request(
        ApprovalRequest(
            request_type=None,
            device_id=b"",
            profile=None,
            auth_meta=[],
            cryptographic_id=b"",
        )
    )


def test_false():
    rejection = RejectRule({"rule_id": "void pointer"})
    assert not rejection.approve_request(None)
    assert not rejection.approve_request(True)
    assert not rejection.approve_request(
        ApprovalRequest(
            request_type=None,
            device_id=b"",
            profile=None,
            auth_meta=[],
            cryptographic_id=b"",
        )
    )
