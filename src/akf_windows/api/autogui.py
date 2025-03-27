"""
The API for the RPyC service exposing PyAutoGUI.
"""

from typing import TYPE_CHECKING

from akf_windows.api._base import WindowsServiceAPI

if TYPE_CHECKING:
    # pyautogui exposes all of its functionality directly through the module
    # instead of a class. in turn, we import it as a "type" for type checkers
    # to provide type hinting while preserving the fact that we're exposing/using
    # the module directly.
    import pyautogui as PyAutoGUIType


class PyAutoGuiServiceAPI(WindowsServiceAPI):
    """
    The service API for interacting with pyautogui (and performing related
    input-based actions).

    You can interact with the remote pyautogui instance using the `pyautogui`
    instance attribute. Note that because pyautogui is a module, all connections
    to the same service will "share" the same resources/configuration. You can
    spin up multiple instances of this service to have separate configurations.
    You can do this by simply calling `start_service()` on the dispatch service.

    You can freely interact with the remote browser instance using the `browser`
    instance attribute.

    TODO: Concrete methods that generate CASE objects? Technically not needed
    for declarative stuff, because we can just use it directly
    """

    def __init__(self, host: str, port: int) -> None:
        super().__init__(host, port)

        # Expose the pyautogui module created on connection
        self.pyautogui: "PyAutoGUIType" = self.rpyc_conn.root.pyautogui


if __name__ == "__main__":
    # Test the client.
    # python -m akf_windows.api.autogui

    # with PyAutoGuiServiceAPI.auto_connect("192.168.50.4") as autogui:
    # with PyAutoGuiServiceAPI.auto_connect("localhost") as autogui:
    with PyAutoGuiServiceAPI("localhost", 18861) as autogui:
        autogui.pyautogui.hotkey("win", "r")
