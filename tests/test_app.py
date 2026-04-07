from lib.helpers import normalize_url, format_volume, find_app


class TestNormalizeUrl:
    def test_adds_https(self):
        assert normalize_url("example.com") == "https://example.com"

    def test_preserves_https(self):
        assert normalize_url("https://example.com") == "https://example.com"

    def test_preserves_http(self):
        assert normalize_url("http://example.com") == "http://example.com"


class TestFormatVolume:
    def test_normal(self):
        assert format_volume(25, False) == "Vol: 25"

    def test_muted(self):
        assert format_volume(25, True) == "Vol: 25 [MUTE]"

    def test_zero(self):
        assert format_volume(0, False) == "Vol: 0"


class TestFindApp:
    APPS = {
        "youtube.leanback.v4": {"title": "YouTube"},
        "com.webos.app.browser": {"title": "Web Browser"},
        "com.webos.app.settings": {"title": "Settings"},
    }

    def test_match_by_title(self):
        result = find_app(self.APPS, "youtube")
        assert result[0] == "youtube.leanback.v4"

    def test_match_by_app_id(self):
        result = find_app(self.APPS, "com.webos.app.browser")
        assert result[0] == "com.webos.app.browser"

    def test_case_insensitive(self):
        result = find_app(self.APPS, "YOUTUBE")
        assert result is not None

    def test_no_match(self):
        assert find_app(self.APPS, "netflix") is None

    def test_partial_match(self):
        result = find_app(self.APPS, "browser")
        assert result[0] == "com.webos.app.browser"
