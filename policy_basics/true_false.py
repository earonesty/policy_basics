# SPDX-FileCopyrightText: © Atakama, Inc <support@atakama.com>
# SPDX-License-Identifier: LGPL-3.0-or-later

from atakama import RulePlugin, ApprovalRequest


class ApproveRule(RulePlugin):
    """
    Rule to accept all requests.

    Accepts no YML Arguments.
    """

    @staticmethod
    def name() -> str:
        return "approve-rule"

    def approve_request(self, request: ApprovalRequest) -> True:
        return True


class RejectRule(RulePlugin):
    """
    Rule to reject all requests

    Accept no YML Arguments.
    """

    @staticmethod
    def name() -> str:
        return "reject-rule"

    def approve_request(self, request: ApprovalRequest) -> False:
        return False
