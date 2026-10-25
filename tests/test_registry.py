from daily_dev_tools.cli import build_parser
from daily_dev_tools.registry import COMMANDS


def test_pack_de_ejemplo_registrado():
    for name in ("gfp", "gcp", "gco", "gsync", "gs", "gl", "groot", "ggl"):
        assert name in COMMANDS


def test_comandos_de_admin_no_generan_alias():
    for name in ("setup", "reload", "teardown", "new", "list", "doctor"):
        assert COMMANDS[name].shortcut is False


def test_alias_son_los_shortcuts_nomas():
    aliases = [c.name for c in COMMANDS.values() if c.shortcut]
    assert "gfp" in aliases
    assert "setup" not in aliases


def test_gfp_con_rama_y_flag():
    ns = build_parser().parse_args(["gfp", "develop", "--checkout"])
    assert ns.branch == "develop"
    assert ns.checkout is True
    assert ns.remote == "origin"


def test_gfp_sin_args_usa_defaults():
    ns = build_parser().parse_args(["gfp"])
    assert ns.branch is None
    assert ns.checkout is False


def test_gcp_acepta_varios_commits():
    ns = build_parser().parse_args(["gcp", "develop", "abc", "def", "--no-pull"])
    assert ns.branch == "develop"
    assert ns.commits == ["abc", "def"]
    assert ns.no_pull is True


def test_gco_con_create():
    ns = build_parser().parse_args(["gco", "develop", "-b"])
    assert ns.branch == "develop"
    assert ns.create is True


def test_gcp_sin_commits_es_error_de_uso():
    import pytest

    with pytest.raises(SystemExit):
        build_parser().parse_args(["gcp", "develop"])
