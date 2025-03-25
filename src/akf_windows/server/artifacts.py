"""
Implementation of the RPyC service for collecting various Windows artifacts.
"""

import logging

# import psutil
from akflib.core.agents.server import AKFService
from caselib.uco.observable import WindowsPrefetch

# from akf_windows.server._util import get_appdata_local_path

logger = logging.getLogger(__name__)


class WindowsArtifactService(AKFService):
    """
    Allows you to interact with a Microsoft Edge browser instance.

    Use the `WindowsArtifactServiceAPI` class to connect to and interact with this service.
    """

    def collect_prefetch(self) -> list[WindowsPrefetch]:
        """
        Scan the machine for Prefetch files and generate a list of `WindowsPrefetch`
        objects.
        """
        raise NotImplementedError


if __name__ == "__main__":
    # cd agents/windows
    # python -m browser.chromium

    # Start the server for testing. All attributes of the service are exposed,
    # since we assume that connections are trusted.
    from rpyc.utils.server import ThreadedServer

    t = ThreadedServer(
        WindowsArtifactService, port=18861, protocol_config={"allow_all_attrs": True}
    )
    print("Starting WindowsArtifact service on port 18861")
    t.start()
