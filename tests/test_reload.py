from daily_dev_tools.shell import generate, install


def test_reload_regenera_shortcuts(tmp_path, monkeypatch):
    monkeypatch.setattr(generate, "CONFIG_DIR", tmp_path)
    target = tmp_path / "shortcuts.sh"
    monkeypatch.setattr(generate, "SHORTCUTS_FILE", target)

    assert install.reload() == 0

    content = target.read_text(encoding="utf-8")
    assert "gaw()" in content
    assert "ddt-reload()" in content
