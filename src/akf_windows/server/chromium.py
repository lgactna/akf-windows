"""
Interact with Chromium browsers using Playwright.
"""

import logging
from typing import Literal

import psutil
import rpyc
from akflib.core.agents.server import AKFService
from playwright.sync_api import BrowserContext, sync_playwright

from akf_windows.server._util import get_appdata_local_path

logger = logging.getLogger(__name__)


class ChromiumService(AKFService):
    """
    Allows you to interact with a Microsoft Edge browser instance.

    Use the `ChromiumServiceAPI` class to connect to and interact with this service.
    """

    def on_connect(self, conn: rpyc.Connection) -> None:
        """
        Start the Playwright instance when a connection is made.

        Expose both the Playwright instance and the browser context to the client.
        """
        self.playwright = sync_playwright().start()

        # Although this may be `None` internally, the expectation is that
        # RPyC clients will only ever see this as non-`None` values.
        self.browser: BrowserContext | None = None

    def on_disconnect(self, conn: rpyc.Connection) -> None:
        """
        Close the browser and stop the Playwright instance when the connection
        is closed.
        """
        if self.browser is not None:
            self.browser.close()
            self.browser = None

        self.playwright.stop()

    def exposed_set_browser(
        self, browser_type: Literal["msedge", "chrome"], profile: str = "Default"
    ) -> BrowserContext:
        """
        Set the browser to use for this service.

        :param browser: The browser to use (which corresponds to the distribution
            channel).
        :param profile: The profile to use for the browser. Defaults to "Default".
            Note that the profile must already exist.
        """
        if self.browser is not None:
            self.browser.close()
            self.browser = None

        if browser_type == "chrome":
            # Use the Chrome profile path
            profile_path = get_appdata_local_path() / "Google" / "Chrome" / "User Data"
        elif browser_type == "msedge":
            # Use the Edge profile path
            profile_path = get_appdata_local_path() / "Microsoft" / "Edge" / "User Data"
        else:
            raise ValueError(f"Unsupported browser type: {browser_type}")

        chromium = self.playwright.chromium
        self.browser = chromium.launch_persistent_context(
            headless=False,
            user_data_dir=profile_path,
            channel=browser_type,
            args=[f"--profile-directory={profile}"],
        )

        return self.browser

    def exposed_kill_edge(self) -> None:
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
        for proc in psutil.process_iter(["name"]):
            if proc.info["name"] == "msedge.exe":
                logger.info(f"Killing Edge process {proc.pid}")
                try:
                    proc.kill()
                except psutil.NoSuchProcess:
                    logger.info(f"Process {proc.pid} is already dead...")


if __name__ == "__main__":
    # cd agents/windows
    # python -m browser.chromium

    # Start the server for testing. All attributes of the service are exposed,
    # since we assume that connections are trusted.
    from rpyc.utils.server import ThreadedServer

    t = ThreadedServer(
        ChromiumService, port=18861, protocol_config={"allow_all_attrs": True}
    )
    print("Starting Chromium service on port 18861")
    t.start()
