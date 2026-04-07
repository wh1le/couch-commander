def __getattr__(name):
    if name == "TVConnection":
        from lib.connection import TVConnection
        return TVConnection
    if name in ("TVRemote", "main"):
        from lib.app import TVRemote, main
        return TVRemote if name == "TVRemote" else main
    raise AttributeError(f"module 'lib' has no attribute {name!r}")
