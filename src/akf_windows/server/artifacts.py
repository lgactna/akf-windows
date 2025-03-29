"""
Implementation of the RPyC service for collecting various Windows artifacts.
"""

import logging
import pickle
import re
from pathlib import Path

# import psutil
from akflib.core.agents.server import AKFService
from caselib.uco.observable import (
    File,
    FileFacet,
    ObservableObject,
    Volume,
    VolumeFacet,
    WindowsPrefetch,
    WindowsPrefetchFacet,
)

from akf_windows.server._util import get_systemroot_path
from akf_windows.server.prefetch.windowsprefetch import Prefetch

logger = logging.getLogger(__name__)


class WindowsArtifactService(AKFService):
    """
    Allows you to generate various CASE objects from Windows artifacts.

    Use the `WindowsArtifactServiceAPI` class to connect to and interact with this service.
    """

    def _parse_single_prefetch_file(
        self, prefetch_path: Path, include_volume: bool = False
    ) -> WindowsPrefetch | None:
        """
        Generate a WindowsPrefetch object from a single prefetch file.

        `include_volume` allows you to tie the Prefetch object to a Volume object.
        This is disabled by default because this function will generate many
        Volume objects that all represent the same actual volume if this function
        is run many times - if you have logic to de-duplicate these entries over
        your entire bundle, you can enable this.

        :param prefetch_path: The path to the prefetch file.
        :param include_volume: Whether to include volume information in the facet.
        :return: A WindowsPrefetch object representing the prefetch file.
        """
        # Check that the file exists and isn't empty
        if not prefetch_path.is_file():
            logger.warning(f"Prefetch file does not exist: {prefetch_path}")
            return None

        if prefetch_path.stat().st_size == 0:
            logger.warning(f"Prefetch file is empty: {prefetch_path}")
            return None

        # Parse the prefetch file
        prefetch_obj = Prefetch(prefetch_path)

        # Generate volume objects, collect volume names so they can be removed
        # from strings where needed. `volume_objs` is a dictionary of volume names
        # (not serial numbers) to Volume objects.
        volume_objs: dict[str, Volume] = {}
        for volume in prefetch_obj.volumesInformationArray:
            volume_name = volume["Volume Name"].decode(
                "UTF-16", errors="backslashreplace"
            )
            serial_number = volume["Serial Number"]

            volume_obj = Volume(hasFacet=[VolumeFacet(volumeID=serial_number)])
            volume_objs[volume_name] = volume_obj

        # Generate actual prefetch facet
        #
        # NOTE: I'm not sure if "firstRun" refers to the first time the application
        # was ever run or if it's the first timestamp entry in the file, but
        # I don't think the first run time *ever* is stored in the prefetch file.
        #
        # The most recent timestamp is the first entry in the list.

        # Generate directory facets
        directories: list[File] = []
        for volume in prefetch_obj.directoryStringsArray:
            for directory_str in volume:
                # Test each volume string, and remove them from the directory
                # string if present. Otherwise, remove anything of the general
                # form "\\Volume{.*?}".
                for volume_name in volume_objs.keys():
                    directory_str = directory_str.replace(volume_name, "")
                directory_str = re.sub(r"\\Volume{.*?}", "", directory_str)

                dir_path = Path(directory_str)

                file_facet = FileFacet(
                    isDirectory=True,
                    fileName=dir_path.name,
                    filePath=str(dir_path.parent),
                )
                directories.append(File(hasFacet=[file_facet]))

        # Generate file facets
        files: list[File] = []
        for resource_str in prefetch_obj.resources:
            # Test each volume string, and remove them from the directory
            # string if present. Otherwise, remove anything of the general
            # form "\\Volume{.*?}".
            for volume_name in volume_objs.keys():
                resource_str = resource_str.replace(volume_name, "")
            resource_str = re.sub(r"\\Volume{.*?}", "", resource_str)

            file_path = Path(resource_str)

            file_facet = FileFacet(
                isDirectory=False,
                fileName=file_path.name,
                filePath=str(file_path.parent),
            )
            files.append(File(hasFacet=[file_facet]))

        # Generate final facet. Note that this only accepts one volume,
        # so we only pick the first volume; I don't know if this will ever
        # have multiple volumes in practice.
        final_volume_obj: ObservableObject | None = None
        if include_volume:
            final_volume_obj = list(volume_objs.values())[0] if volume_objs else None

        facet = WindowsPrefetchFacet(
            volume=final_volume_obj,
            accessedDirectory=directories,
            accessedFile=files,
            firstRun=prefetch_obj.timestamps[-1] if prefetch_obj.timestamps else None,
            lastRun=prefetch_obj.timestamps[0] if prefetch_obj.timestamps else None,
            timesExecuted=prefetch_obj.runCount,
            applicationFileName=prefetch_obj.executableName,
            prefetchHash=prefetch_obj.hash,
        )

        pf = WindowsPrefetch(hasFacet=[facet])

        return pf

    def exposed_collect_prefetch_file(
        self, prefetch_path: Path
    ) -> WindowsPrefetch | None:
        """
        Parse a single prefetch file and generate a WindowsPrefetch object.

        :param prefetch_path: The path to the prefetch file.
        :return: A WindowsPrefetch object representing the prefetch file, or None
            if the file does not exist or is empty.
        """
        return self._parse_single_prefetch_file(prefetch_path)

    def exposed_collect_prefetch_dir(
        self, prefetch_folder: Path | None = None, glob: str = "*.pf"
    ) -> bytes:
        """
        Scan the machine for Prefetch files and generate a list of `WindowsPrefetch`
        objects.

        :param prefetch_folder: The path to the prefetch folder. Defaults to the
            system prefetch folder.
        :param glob: The glob pattern to use for finding prefetch files.
        :return: A list of WindowsPrefetch objects representing the prefetch files.
        """

        # Find the default prefetch folder
        if prefetch_folder is None:
            prefetch_folder = (get_systemroot_path() / "Prefetch").resolve()
        logger.info(f"Scanning for Prefetch files in {prefetch_folder}, {glob=}")

        # Collect all prefetch files
        result: list[WindowsPrefetch] = []
        for prefetch_file in prefetch_folder.glob(glob):
            pf = self._parse_single_prefetch_file(prefetch_file)
            if pf is not None:
                result.append(pf)

        # In theory, we could perform deduplication of the volumes here, but
        # this doesn't guarantee that the volume will be unique over an entire
        # bundle -- for now, we simply will not include volume information with
        # these prefetch files, as it's easier for a caller to tack on a reference
        # to an existing volume after the fact if needed.

        # RPyC doesn't play well with some of the Pydantic properties that we need
        # to correctly add things to AKFBundle using AKFBundle.add_objects, so we
        # pickle the objects and deserialize them on the host.
        return pickle.dumps(result)


if __name__ == "__main__":
    # cd agents/windows
    # python -m browser.chromium

    # Start the server for testing. All attributes of the service are exposed,
    # since we assume that connections are trusted.
    from rpyc.utils.server import ThreadedServer

    t = ThreadedServer(
        WindowsArtifactService, port=18861, protocol_config={"allow_all_attrs": True}
    )
    print("Starting Windows artifact service on port 18861")
    t.start()
