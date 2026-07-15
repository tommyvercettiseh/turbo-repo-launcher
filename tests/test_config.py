from app.config import DEFAULT_SETTINGS


def test_default_settings_shape():
    assert "repo_root" in DEFAULT_SETTINGS
    assert "repos" in DEFAULT_SETTINGS
    assert isinstance(DEFAULT_SETTINGS["repos"], list)
