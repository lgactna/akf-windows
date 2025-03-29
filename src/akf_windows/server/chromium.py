"""
Implementation of the RPyC service for interacting with Chromium browsers using Playwright.
"""

import logging
import pickle
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import psutil
import rpyc
from akflib.core.agents.server import AKFService
from caselib.uco.observable import (
    URL,
    Application,
    ApplicationFacet,
    URLFacet,
    URLHistory,
    URLHistoryEntry,
    URLHistoryFacet,
)
from playwright.sync_api import BrowserContext, sync_playwright
from pydantic import AwareDatetime, BaseModel

from akf_windows.server._util import get_appdata_local_path

logger = logging.getLogger(__name__)


class BrowserHistoryEntry(BaseModel):
    """Pydantic model representing an entry in Chrome/Edge's urls table"""

    id: int
    url: str
    title: str
    visit_count: int
    typed_count: int
    last_visit_time: AwareDatetime
    hidden: bool = False

    def to_case_object(self) -> URLHistoryEntry:
        """
        Convert this entry to a valid URLHistoryEntry CASE object.

        The structure of this object is consistent with that of the URLHistory
        example object provided with the CASE Ontology gallery:
        https://caseontology.org/examples/owl_trafficking/

        Note that unlike the CASE example, this function does not use a
        reference to the URL object; it is assumed to be globally unique.
        (That is, URLHistoryEntry.url is *not* a reference; it is the complete,
        original object with a URLFacet.)

        You should add this to an existing URLHistoryFacet object under its
        urlHistoryEntry attribute.

        Special notes:
        - Any fields set to None are not recorded in Chromium history files.
        - browserUserProfile is a string, but is likely intended to be a reference.
          It is set to None here.
        """

        return URLHistoryEntry(
            url=URL(hasFacet=[URLFacet(fullValue=self.url)]),
            referrerUrl=None,
            expirationTime=None,
            firstVisit=None,
            lastVisit=self.last_visit_time,
            manuallyEnteredCount=self.typed_count,
            visitCount=self.visit_count,
            browserUserProfile=None,
            hostname=None,
            pageTitle=self.title,
            keywordSearchTerm=None,
        )


def get_chrome_history_path() -> Path:
    return (
        get_appdata_local_path()
        / "Google"
        / "Chrome"
        / "User Data"
        / "Default"
        / "History"
    )


def get_edge_history_path() -> Path:
    return (
        get_appdata_local_path()
        / "Microsoft"
        / "Edge"
        / "User Data"
        / "Default"
        / "History"
    )


def chromium_timestamp_to_datetime(timestamp: int) -> datetime:
    """
    Convert Chromium's timestamp format to Python datetime.
    Chromium timestamps are microseconds since Jan 1, 1601 UTC.
    """
    # Difference between Chrome's epoch and Unix epoch (seconds)
    epoch_difference = 11644473600

    # Convert from microseconds to seconds and adjust for epoch difference
    unix_timestamp = timestamp / 1000000 - epoch_difference

    # print(unix_timestamp)

    # Convert to datetime
    return datetime.fromtimestamp(unix_timestamp, UTC)


def parse_browser_history(
    browser_type: Literal["chrome", "msedge"], history_path: Path | None = None
) -> list[BrowserHistoryEntry]:
    """Parse browser history and return a list of BrowserHistoryEntry objects"""
    if history_path is None:
        if browser_type == "chrome":
            history_path = get_chrome_history_path()
        elif browser_type == "msedge":
            history_path = get_edge_history_path()
        else:
            raise ValueError(f"Unsupported browser type: {browser_type}")

    # Browser locks the database when it's open, so make a copy
    temp_history_path = history_path.with_suffix(".temp")

    try:
        # Check if history exists
        if not history_path.exists():
            raise FileNotFoundError(
                f"{browser_type} history not found at {history_path}"
            )

        # Copy the file to avoid lock issues
        with open(history_path, "rb") as src, open(temp_history_path, "wb") as dst:
            dst.write(src.read())

        # Connect to the copied database
        conn = sqlite3.connect(temp_history_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Query the urls table
        cursor.execute(
            """
            SELECT id, url, title, visit_count, typed_count, last_visit_time, hidden
            FROM urls
            ORDER BY last_visit_time DESC
        """
        )

        history_entries = []
        for row in cursor.fetchall():
            try:
                last_visit = chromium_timestamp_to_datetime(row["last_visit_time"])
            except OSError:
                # The timestamp value is invalid, so we ignore it altogether
                logger.error(
                    f"Got invalid timestamp value for {row['id']=}, {row['url']=}: {row['last_visit_time']=}"
                )
                continue

            entry = BrowserHistoryEntry(
                id=row["id"],
                url=row["url"],
                title=row["title"] or "",  # Handle potential NULL values
                visit_count=row["visit_count"],
                typed_count=row["typed_count"],
                last_visit_time=last_visit,
                hidden=bool(row["hidden"]),
            )

            history_entries.append(entry)

        return history_entries

    finally:
        # Clean up the temporary copy
        if temp_history_path.exists():
            try:
                temp_history_path.unlink()
            except PermissionError:
                pass  # Ignore if we can't delete the file


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

    def exposed_get_history(
        self, browser_type: Literal["chrome", "msedge"], history_path: Path | None
    ) -> bytes:
        """
        Get browser history entries for the specified browser.

        :param browser_type: Type of browser to retrieve history from ("chrome" or "msedge")
        :param history_path: Path to the browser history file. If None, defaults
            to the standard location for the specified browser.
        :return: A URLHistory object containing the browser history entries.
        """
        browser_entries = parse_browser_history(browser_type, history_path)

        # Convert these Pydantic models to CASE objects
        url_history_entries = [obj.to_case_object() for obj in browser_entries]

        # Create Application object for this browser (note that it also won't
        # be included as a reference, it'll be the original)
        app_obj = Application(
            hasFacet=[ApplicationFacet(applicationIdentifier=browser_type)],
        )

        url_history = URLHistory(
            hasFacet=[
                URLHistoryFacet(
                    urlHistoryEntry=url_history_entries, browserInformation=app_obj
                )
            ],
        )

        # Pickle the object to send it over RPyC
        return pickle.dumps(url_history)


if __name__ == "__main__":
    # Start the server for testing. All attributes of the service are exposed,
    # since we assume that connections are trusted.
    from rpyc.utils.server import ThreadedServer

    t = ThreadedServer(
        ChromiumService, port=18861, protocol_config={"allow_all_attrs": True}
    )
    print("Starting Chromium service on port 18861")
    t.start()
