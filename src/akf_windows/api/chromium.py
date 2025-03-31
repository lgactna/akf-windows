"""
The API for the RPyC service exposing Microsoft Edge.
"""

import pickle
import time
from pathlib import Path
from typing import Literal

from caselib.uco.observable import URLHistory
from playwright.sync_api import BrowserContext

from akf_windows.api._base import WindowsServiceAPI


class ChromiumServiceAPI(WindowsServiceAPI):
    """
    The service API for interacting with Microsoft Edge using Playwright.

    You can freely interact with the remote browser instance using the `browser`
    instance attribute.

    TODO: Even though we expose `BrowserContext`, we should still have a small
    number of "concrete" methods, like `goto()`, which leverage the CASE
    library and automatically create/return CASE entries.
    """

    related_service = "ChromiumService"

    def __init__(self, host: str, port: int) -> None:
        super().__init__(host, port)

        # Expose the browser context that's created on connection
        self.browser: BrowserContext = self.rpyc_conn.root.browser

    def set_browser(
        self, browser_type: Literal["msedge", "chrome"], profile: str = "Default"
    ) -> BrowserContext:
        """
        Set the browser to use for this service.

        If the browser is currently open, it will be closed.

        :param browser: The browser to use (which corresponds to the distribution
            channel).
        :param profile: The profile to use for the browser. Defaults to "Default".
            Note that the profile must already exist.
        """
        self.browser = self.rpyc_conn.root.set_browser(browser_type, profile)
        return self.browser

    def kill_edge(self) -> None:
        """
        Kill Edge process instances by name.

        By default, Edge has a feature called "startup boost" that keeps a background
        process running after the GUI itself has closed. This prevents another
        browser window with the same profile from being opened and raises fairly
        confusing errors from Playwright ("Target page, context or browser has been
        closed").

        This method kills all Edge processes by name, which effectively bypasses
        the "startup boost" feature. In general, this is only necessary if Edge
        has been opened through other means (e.g. manually).
        """
        self.rpyc_conn.root.kill_edge()

    def get_history(
        self, browser_type: Literal["chrome", "msedge"], history_path: Path | None = None
    ) -> URLHistory:
        """
        Get browser history entries for the specified browser.

        :param browser_type: Type of browser to retrieve history from ("chrome" or "msedge")
        :param history_path: Path to the browser history file. If None, defaults
            to the standard location for the specified browser.
        :return: A URLHistory object containing the browser history entries.
        """
        # The result is pickled, and must be unpickled to be used.
        return pickle.loads(self.rpyc_conn.root.get_history(browser_type, history_path))


if __name__ == "__main__":
    # Test the client.
    # python -m akf_windows.api.chromium

    from akflib.rendering.objs import AKFBundle

    # auto-connect doesn't work, but standard connection does?
    # with ChromiumServiceAPI("localhost", 18861) as chromium:
    # with ChromiumServiceAPI.auto_connect("localhost") as chromium:
    with ChromiumServiceAPI.auto_connect("192.168.50.4") as chromium:
        chromium.kill_edge()
        chromium.set_browser("msedge")
        assert chromium.browser is not None

        page = chromium.browser.new_page()

        page.goto("http://example.com")
        time.sleep(5)

        page.goto("http://google.com")
        time.sleep(5)

        obj = chromium.get_history("msedge", None)

        # Browser closes automatically as part of the context manager

    print(obj.hasFacet[0].browserInformation)

    bundle = AKFBundle()
    bundle.add_object(obj)

    for obj_type, objs in bundle._object_index.items():
        print(f"{obj_type}: {len(objs)}")

    # print(type(bundle))
    print(len(bundle.object))
    # print(bundle.object)
    # print(bundle)
