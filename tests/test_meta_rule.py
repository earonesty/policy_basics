from atakama import ApprovalRequest, MetaInfo

from policy_basics.meta_str import MetaRule


def meta(*paths, complete=True):
    return ApprovalRequest(
        request_type=None,
        device_id=b"whatever",
        profile=None,
        auth_meta=[MetaInfo(p, complete) for p in paths],
    )


def test_paths():
    pr = MetaRule({"paths": ["sub/path", "/root/sub", "*.ext", "basename.*"]})
    assert pr.approve_request(meta("/root/sub/path/basename.ext"))
    assert pr.approve_request(meta("whatever.ext"))
    assert pr.approve_request(meta("/root/sub/xxx"))
    assert pr.approve_request(meta("sdfjksdfjk/sub/path/sdfsdfj"))
    assert pr.approve_request(meta("/basename.xxx"))
    # insensitive
    assert pr.approve_request(meta("/Root/Sub/Path/Basename.ext"))
    assert not pr.approve_request(meta("/root/sub/path/basename.ext", "/some/other"))
    # sub paths must be sub paths
    assert not pr.approve_request(meta("sub/path"))
    assert not pr.approve_request(meta("/sub/path.txt"))
    assert pr.approve_request(meta("/sub/path"))
    # sub is ok
    assert pr.approve_request(meta("<incomplete>some/sub/path"))


def test_glob_basename():
    pr = MetaRule({"paths": ["basename.*"]})
    assert pr.approve_request(meta("/basename.xxx"))
    assert pr.approve_request(meta("basename.xxx"))
    assert not pr.approve_request(meta("/basename/xxx"))
    assert not pr.approve_request(meta("/basename.xxx/yyy"))
    assert not pr.approve_request(meta("/basename.xxx/"))


def test_glob_subcomponent():
    pr = MetaRule({"paths": ["sub/co*mp"]})
    assert pr.approve_request(meta("root/sub/comp/basename"))
    assert pr.approve_request(meta("root/sub/co77mp/basename"))
    assert not pr.approve_request(meta("root/sub/co/mp/basename"))

    pr = MetaRule({"paths": ["little*sub/"]})
    assert pr.approve_request(meta("root/little sub"))
    assert pr.approve_request(meta("root/little sub/comp/basename"))
    assert pr.approve_request(meta("root/littlesub/comp/basename"))
    assert pr.approve_request(meta("root/littlesub/comp/basename"))
    assert not pr.approve_request(meta("root/little/sub"))


def test_sensitive_paths():
    pr = MetaRule(
        {
            "paths": ["sub/path", "/root/sub", "*.ext", "basename.*"],
            "case_sensitive": True,
        }
    )
    assert pr.approve_request(meta("/root/sub/path/basename.ext"))
    assert not pr.approve_request(meta("/Root/Sub/Path/Basename.Ext"))


def test_meta_regex():
    pr = MetaRule({"regexes": ["reg.*ex"]})
    assert pr.approve_request(meta("reg777ex"))


def test_meta_invert():
    pr = MetaRule({"regexes": ["!regex"]})
    assert pr.approve_request(meta("nomatch"))
    assert not pr.approve_request(meta("regex"))
    pr = MetaRule({"paths": ["!sub/path"]})
    assert pr.approve_request(meta("/anywhere/else"))
    assert not pr.approve_request(meta("root/sub/path"))
    assert pr.approve_request(meta("/sub/path.txt"))
    assert not pr.approve_request(meta("/sub/path"))


def test_require_complete():
    pr = MetaRule(
        {
            "paths": ["sub/path", "/root/sub", "*.ext", "basename.*"],
            "require_complete": True,
        }
    )
    assert not pr.approve_request(meta("/root/sub/path/basename.ext", complete=False))
    assert pr.approve_request(meta("/root/sub/path/basename.ext", complete=True))
