"""
The API for the RPyC service that locates and collects Windows artifacts,
constructing and returning CASE objects.
"""

from pathlib import Path

from caselib.uco.observable import WindowsPrefetch

from akf_windows.api._base import WindowsServiceAPI


class WindowsArtifactServiceAPI(WindowsServiceAPI):
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

    def collect_prefetch_file(self, prefetch_path: Path) -> WindowsPrefetch | None:
        """
        Collect a WindowsPrefetch object from a prefetch file.

        :param prefetch_path: The path to the prefetch file.
        :return: A WindowsPrefetch object representing the prefetch file, or None
            if the file does not exist or is empty.
        """
        return self.rpyc_conn.root.collect_prefetch_file(prefetch_path)
    
    def collect_prefetch_dir(self, prefetch_folder: Path | None = None) -> list[WindowsPrefetch]:
        """
        Collect WindowsPrefetch objects from the prefetch directory.

        :param prefetch_folder: The path to the prefetch folder. Defaults to the
            system prefetch folder.
        :return: A list of WindowsPrefetch objects representing the prefetch files.
        """
        return self.rpyc_conn.root.collect_prefetch_dir(prefetch_folder)
        


if __name__ == "__main__":
    # Test the client.
    # python -m akf_windows.api.autogui

    # with PyAutoGuiServiceAPI.auto_connect("192.168.50.4") as autogui:
    # with PyAutoGuiServiceAPI.auto_connect("localhost") as autogui:
    with WindowsArtifactServiceAPI("localhost", 18861) as win_artifact:
        print(win_artifact.collect_prefetch_dir())

