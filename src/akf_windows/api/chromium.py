"""
The API for the RPyC service exposing Microsoft Edge.
"""

import time
from typing import Literal

from akflib.core.agents.client import AKFServiceAPI
from playwright.sync_api import BrowserContext


class ChromiumServiceAPI(AKFServiceAPI):
    """
    The service API for interacting with Microsoft Edge using Playwright.

    You can freely interact with the remote browser instance using the `browser`
    instance attribute.
    """

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


if __name__ == "__main__":
    # python -m akf.agents.windows.chromium

    # Test the client
    with ChromiumServiceAPI("localhost", 18861) as chromium:
        # Open a new Edge browser
        chromium.set_browser("msedge")
        assert chromium.browser is not None

        page = chromium.browser.new_page()

        page.goto("http://example.com")
        time.sleep(5)

        page.goto("http://google.com")
        time.sleep(5)

        # Browser closes automatically as part of the context manager
