# SPDX-FileCopyrightText: © Atakama, Inc <support@atakama.com>
# SPDX-License-Identifier: LGPL-3.0-or-later

from collections import defaultdict
from typing import Optional, Dict, List, Tuple, Set

from atakama import RulePlugin, ApprovalRequest

MINIMUM_WORD_COUNT = 4


class ProfileIdRule(RulePlugin):
    """
    Basic rule for exact match of profile ids:

    YML Arguments:
     - profile_ids:
        - profile_id_in_hex
        - profile words space delimited

    ```
    Example:
        - rule: profile-id-rule
          profile_ids:
            - d56e89af673fe1897fdcc8
            - correct horse battery staple diamond hands
    ```
    """

    @staticmethod
    def name() -> str:
        return "profile-id-rule"

    def __init__(self, args):
        self.__pids: Set[bytes] = set()
        self.__wkey: Dict[int, Set[Tuple]] = defaultdict(set)
        for pid in args["profile_ids"]:
            if " " in pid:
                words = tuple(w.strip() for w in pid.split(" "))
                assert (
                    len(words) >= MINIMUM_WORD_COUNT
                ), "profile id word match must use at least 4 words"
                self.__wkey[len(words)].add(words)
            else:
                pid = bytes.fromhex(pid)
                self.__pids.add(pid)

        super().__init__(args)

    def approve_request(self, request: ApprovalRequest) -> Optional[bool]:
        if request.profile.profile_id in self.__pids:
            return True
        if self._word_match(request.profile.profile_words):
            return True
        return False

    def _word_match(self, words: List[str]) -> bool:
        for wlen, wset in self.__wkey.items():
            if tuple(words[0:wlen]) in wset:
                return True
        return False
