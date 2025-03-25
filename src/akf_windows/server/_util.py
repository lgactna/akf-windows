import os
from pathlib import Path


def get_appdata_roaming_path() -> Path:
    """
    Get the path to the AppData directory for the current user.
    """
    appdata_dir = os.getenv("APPDATA")
    assert appdata_dir is not None

    if appdata_dir is None:
        raise Exception("Could not find the APPDATA environment variable")

    return Path(appdata_dir).resolve()


def get_appdata_local_path() -> Path:
    """
    Get the path to the AppData directory for the current user.
    """
    appdata_dir = os.getenv("LOCALAPPDATA")
    assert appdata_dir is not None

    if appdata_dir is None:
        raise Exception("Could not find the LOCALAPPDATA environment variable")

    return Path(appdata_dir).resolve()
