import json
import lib.config as config


def test_load_key_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "KEY_FILE", str(tmp_path / "nonexistent.json"))
    assert config.load_key("1.2.3.4") is None


def test_load_key_invalid_json(tmp_path, monkeypatch):
    bad = tmp_path / "keys.json"
    bad.write_text("not json")
    monkeypatch.setattr(config, "KEY_FILE", str(bad))
    assert config.load_key("1.2.3.4") is None


def test_save_and_load_key(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "KEY_FILE", str(tmp_path / "keys.json"))
    config.save_key("abc123", "1.2.3.4")
    assert config.load_key("1.2.3.4") == "abc123"


def test_save_key_preserves_other_keys(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "KEY_FILE", str(tmp_path / "keys.json"))
    config.save_key("key_a", "10.0.0.1")
    config.save_key("key_b", "10.0.0.2")
    assert config.load_key("10.0.0.1") == "key_a"
    assert config.load_key("10.0.0.2") == "key_b"


def test_save_key_overwrites_existing(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "KEY_FILE", str(tmp_path / "keys.json"))
    config.save_key("old", "1.2.3.4")
    config.save_key("new", "1.2.3.4")
    assert config.load_key("1.2.3.4") == "new"


def test_save_key_creates_directory(tmp_path, monkeypatch):
    path = tmp_path / "sub" / "dir" / "keys.json"
    monkeypatch.setattr(config, "KEY_FILE", str(path))
    config.save_key("abc", "1.2.3.4")
    assert path.exists()
    assert config.load_key("1.2.3.4") == "abc"


def test_load_key_default_ip(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "KEY_FILE", str(tmp_path / "keys.json"))
    config.save_key("default_key", config.TV_IP)
    assert config.load_key() == "default_key"


def test_load_key_unknown_ip(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "KEY_FILE", str(tmp_path / "keys.json"))
    config.save_key("abc", "1.2.3.4")
    assert config.load_key("9.9.9.9") is None
