"""
Implementation of the RPyC service for interacting with the VM using PyAutoGUI.
"""

import logging
from typing import TYPE_CHECKING

from akflib.core.agents.server import AKFService
import pyautogui
import rpyc

logger = logging.getLogger(__name__)

if TYPE_CHECKING: 
    # pyautogui exposes all of its functionality directly through the module 
    # instead of a class. in turn, we import it as a "type" for type checkers
    # to provide type hinting while preserving the fact that we're exposing/using
    # the module directly.
    import pyautogui as PyAutoGUIType

class PyAutoGuiService(AKFService):
    """
    Allows you to invoke pyautogui commands on the VM.
    
    pyautogui exposes everything directly through the module, rather than a class.
    in theory, this means two things:
    - all connections to this service will share the same resources/configuration
      (e.g. the setting of pyautogui.PAUSE or pyautogui.FAILSAFE) since we're using
      ThreadedServer -- but you can spin up multiple instances of this service,
      which will not share the same resources

    Use the `PyAutoGuiServiceAPI` class to connect to and interact with this service.
    """
    
    def on_connect(self, conn: rpyc.Connection) -> None:
        """
        Expose the pyautogui module to clients.
        """
        self.pyautogui: "PyAutoGUIType" = pyautogui


if __name__ == "__main__":
    # Start the server for testing. All attributes of the service are exposed,
    # since we assume that connections are trusted.
    from rpyc.utils.server import ThreadedServer

    t = ThreadedServer(
        PyAutoGuiService, port=18861, protocol_config={"allow_all_attrs": True}
    )
    print("Starting PyAutoGui service on port 18861")
    t.start()
