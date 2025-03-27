"""
Declarative modules for collecting Windows artifacts.
"""

import logging
from pathlib import Path
from typing import Any, ClassVar

from akflib.core.hypervisor.base import HypervisorABC
from akflib.declarative.core import AKFModule, AKFModuleArgs, NullArgs, NullConfig
from akflib.declarative.util import auto_format
from akflib.rendering.objs import AKFBundle

from akf_windows.api.artifacts import WindowsArtifactServiceAPI

logger = logging.getLogger(__name__)


class WindowsArtifactStartModule(AKFModule[NullArgs, NullConfig]):
    """
    Create a persistent WindowsArtifactServiceAPI object.

    State variables:
    - akflib.hypervisor (read): to get the IP of the currently active virtual machine.
    - akf_windows.artifacts.artifact_service (write): Set to the name of the
      WindowsArtifactServiceAPI variable on generation; set to an instance of
      WindowsArtifactServiceAPI on execution.
    """

    aliases = ["artifact_service_start"]
    arg_model = NullArgs
    config_model = NullConfig

    dependencies: ClassVar[set[str]] = {
        "akf_windows.api.artifacts.WindowsArtifactServiceAPI"
    }

    @classmethod
    def generate_code(
        cls, args: NullArgs, config: NullConfig, state: dict[str, Any]
    ) -> str:
        if "akf_windows.artifacts.artifact_service" in state:
            logger.warning("WindowsArtifactServiceAPI object already exists, skipping")
            return ""

        hypervisor_var = cls.get_hypervisor_var(state)
        if hypervisor_var is None:
            raise ValueError(
                "State variable `akflib.hypervisor_var` not available, can't determine IP"
            )

        # Set new state variables
        state["akf_windows.artifacts.artifact_service"] = "win_artifact"

        return auto_format(
            f"win_artifact = WindowsArtifactServiceAPI.auto_connect({hypervisor_var}.get_maintenance_ip())",
            state,
        )

    @classmethod
    def execute(
        cls,
        args: NullArgs,
        config: NullConfig,
        state: dict[str, Any],
    ) -> None:
        if "akf_windows.artifacts.artifact_service" in state:
            logger.warning("WindowsArtifactServiceAPI object already exists, skipping")
            return

        hypervisor = cls.get_hypervisor(state)
        if hypervisor is None:
            raise ValueError(
                "State variable `akflib.hypervisor` not available, can't determine IP"
            )
        assert isinstance(hypervisor, HypervisorABC)

        win_artifact = WindowsArtifactServiceAPI.auto_connect(
            hypervisor.get_maintenance_ip()
        )

        state["akf_windows.artifacts.artifact_service"] = win_artifact
        logger.info("Created WindowsArtifactServiceAPI object")


class WindowsArtifactStopModule(AKFModule[NullArgs, NullConfig]):
    """
    Stop the persistent WindowsArtifactServiceAPI object.

    State variables:
    - akf_windows.artifacts.artifact_service (read/write): Closed and/or
      cleared from state.
    """

    aliases = ["artifact_service_stop"]
    arg_model = NullArgs
    config_model = NullConfig

    dependencies: ClassVar[set[str]] = {
        "akf_windows.api.artifacts.WindowsArtifactServiceAPI"
    }

    @classmethod
    def generate_code(
        cls, args: NullArgs, config: NullConfig, state: dict[str, Any]
    ) -> str:
        if "akf_windows.artifacts.artifact_service" not in state:
            logger.warning("WindowsArtifactServiceAPI object doesn't exist, skipping")
            return ""

        var_name = state["akf_windows.artifacts.artifact_service"]
        del state["akf_windows.artifacts.artifact_service"]

        return auto_format(
            f"{var_name}.rpyc_conn.close()",
            state,
        )

    @classmethod
    def execute(
        cls,
        args: NullArgs,
        config: NullConfig,
        state: dict[str, Any],
        bundle: AKFBundle | None = None,
    ) -> None:
        if "akf_windows.artifacts.artifact_service" not in state:
            logger.warning("WindowsArtifactServiceAPI object doesn't exist, skipping")
            return

        win_artifact = state["akf_windows.artifacts.artifact_service"]
        assert isinstance(win_artifact, WindowsArtifactServiceAPI)

        win_artifact.rpyc_conn.close()

        del state["akf_windows.artifacts.artifact_service"]
        logger.info("Closed WindowsArtifactServiceAPI object")


class PrefetchModuleArgs(AKFModuleArgs):
    prefetch_folder: Path | None = None


class PrefetchModule(AKFModule[PrefetchModuleArgs, NullConfig]):
    """
    State variables:
    - akflib.hypervisor (read): to get the IP of the currently active virtual machine.
    - akflib.bundle (write): to add the collected prefetch objects.
    - akf_windows.artifacts.artifact_service (read): to re-use an existing
      RPyC connection.
    """

    aliases = ["prefetch"]
    arg_model = PrefetchModuleArgs
    config_model = NullConfig

    dependencies: ClassVar[set[str]] = {"random"}

    @classmethod
    def generate_code(
        cls, args: PrefetchModuleArgs, config: NullConfig, state: dict[str, Any]
    ) -> str:

        result = ""

        # Check that a WindowsArtifactService API object is available. If it isn't,
        # include a temporary context manager, and assert that a `akflib.hypervisor`
        # object is available.
        if "akf_windows.artifacts.artifact_service" not in state:
            if "akflib.hypervisor" not in state:
                raise ValueError(
                    "State variable `akflib.hypervisor` not available, can't determine IP"
                )

            # Generate temporary object. Don't add it to the state and don't modify
            # the indentation; we want it to close as soon as we're done.

            hypervisor_var = state["akflib.hypervisor"]

            result += f"with WindowsArtifactServiceAPI.auto_connect({hypervisor_var}.get_maintenance_ip()) as win_artifact:\n    "
            win_artifact_var = "win_artifact"
        else:
            # Use the existing object.
            win_artifact_var = state["akf_windows.artifacts.artifact_service"]

        result += f"prefetch_objs = {win_artifact_var}.collect_prefetch_dir({args.prefetch_folder})"

        return auto_format(
            result,
            state,
        )

    @classmethod
    def execute(
        cls,
        args: PrefetchModuleArgs,
        config: NullConfig,
        state: dict[str, Any],
        bundle: AKFBundle | None = None,
    ) -> None:

        if bundle is None:
            logger.warning(
                "Executing PrefetchModule without a bundle won't do anything - skipping!"
            )
            return

        # Check that a WindowsArtifactServiceAPI object is available. If it
        # isn't, create a temporary context manager. (This, of course, requires
        # that a machine is available with `akflib.machine`.)
        close_win_artifact = False
        if "akf_windows.artifacts.artifact_service" not in state:
            if "akflib.hypervisor" not in state:
                raise ValueError(
                    "State variable `akflib.hypervisor` not available, can't determine IP"
                )

            hypervisor = state["akflib.hypervisor"]
            assert isinstance(hypervisor, HypervisorABC)

            win_artifact = WindowsArtifactServiceAPI.auto_connect(
                hypervisor.get_maintenance_ip()
            )

            logger.info("Creating temporary WindowsArtifactServiceAPI object")
            close_win_artifact = True
        else:
            win_artifact = state["akf_windows.artifacts.artifact_service"]
            assert isinstance(win_artifact, WindowsArtifactServiceAPI)

        prefetch_objs = win_artifact.collect_prefetch_dir(args.prefetch_folder)
        if close_win_artifact:
            win_artifact.rpyc_conn.close()
            logger.info("Closed temporary WindowsArtifactServiceAPI object")

        # Add all objects to the bundle
        bundle.add_objects(prefetch_objs)
