MOUSE_SENSITIVITY = 1.5


def normalize_url(url):
    """Ensure URL has a scheme."""
    if not url.startswith(("http://", "https://")):
        return "https://" + url
    return url


def format_volume(volume, muted):
    """Format volume label text."""
    return f"Vol: {volume}" + (" [MUTE]" if muted else "")


def find_app(apps, query):
    """Find an app by query matching title or app id. Returns (app_id, app_info) or None."""
    matches = [
        (k, v) for k, v in apps.items()
        if query.lower() in v.get("title", "").lower() or query.lower() in k.lower()
    ]
    return matches[0] if matches else None
