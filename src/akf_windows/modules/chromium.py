# """
# Declarative modules for interacting with Chromium browsers.
# """

# import logging
# from pathlib import Path
# from typing import Any, ClassVar

# from akflib.core.hypervisor.base import HypervisorABC
# from akflib.declarative.core import AKFModule, AKFModuleArgs, NullConfig
# from akflib.declarative.util import auto_format

# from akf_windows.api.chromium import ChromiumServiceAPI
# from akf_windows.modules._base import ServiceStartModule, ServiceStopModule

# logger = logging.getLogger(__name__)


# class ChromiumServiceStartModule(ServiceStartModule):
#     """
#     Create a persistent ChromiumServiceAPI object.

#     State variables:
#     - akflib.hypervisor (read): to get the IP of the currently active virtual machine.
#     - akf_windows.artifacts.chromium_service (write): Set to the name of the
#       ChromiumServiceAPI variable on generation; set to an instance of
#       ChromiumServiceAPI on execution.
#     """

#     aliases = ["chromium_service_start"]

#     dependencies: ClassVar[set[str]] = {"akf_windows.api.chromium.ChromiumServiceAPI"}

#     state_var = "akf_windows.artifacts.chromium_service"
#     service_api_class = ChromiumServiceAPI
#     service_api_var_name = "chromium_service"


# class ChromiumServiceStopModule(ServiceStopModule):
#     """
#     Close a persistent ChromiumServiceAPI object.

#     State variables:
#     - akf_windows.artifacts.chromium_service (read/write): Closed and/or
#       cleared from state.
#     """

#     aliases = ["chromium_service_stop"]

#     dependencies: ClassVar[set[str]] = {"akf_windows.api.chromium.ChromiumServiceAPI"}

#     state_var = "akf_windows.artifacts.chromium_service"
#     service_api_class = ChromiumServiceAPI
#     service_api_var_name = "chromium_service"


# class PrefetchModuleArgs(AKFModuleArgs):
#     prefetch_folder: Path | None = None


# class PrefetchModule(AKFModule[PrefetchModuleArgs, NullConfig]):
#     """
#     State variables:
#     - akflib.hypervisor (read): to get the IP of the currently active virtual machine.
#     - akflib.bundle (write): to add the collected prefetch objects.
#     - akf_windows.artifacts.artifact_service (read): to re-use an existing
#       RPyC connection.
#     """

#     aliases = ["prefetch"]
#     arg_model = PrefetchModuleArgs
#     config_model = NullConfig

#     dependencies: ClassVar[set[str]] = {
#         "akf_windows.api.artifacts.WindowsArtifactServiceAPI"
#     }

#     @classmethod
#     def generate_code(
#         cls, args: PrefetchModuleArgs, config: NullConfig, state: dict[str, Any]
#     ) -> str:
#         bundle_var = cls.get_akf_bundle_var(state)
#         if bundle_var is None:
#             logger.warning(
#                 "Executing PrefetchModule without a bundle won't do anything - skipping!"
#             )
#             return "# No CASE bundle was available, so no code was generated"

#         result = ""

#         # Check that a WindowsArtifactService API object is available. If it isn't,
#         # include a temporary context manager, and assert that a `akflib.hypervisor`
#         # object is available.
#         indent_code = False
#         if "akf_windows.artifacts.artifact_service" not in state:
#             hypervisor_var = cls.get_hypervisor_var(state)
#             if hypervisor_var is None:
#                 raise ValueError(
#                     "State variable `akflib.hypervisor` not available, can't start a service"
#                 )

#             # Generate temporary object. Don't add it to the state and don't modify
#             # the indentation; we want it to close as soon as we're done.
#             indent_code = True
#             result += f"with WindowsArtifactServiceAPI.auto_connect({hypervisor_var}.get_maintenance_ip()) as win_artifact:\n"
#             win_artifact_var = "win_artifact"
#         else:
#             # Use the existing object.
#             win_artifact_var = state["akf_windows.artifacts.artifact_service"]

#         if indent_code:
#             result += f"    prefetch_objs = {win_artifact_var}.collect_prefetch_dir({args.prefetch_folder})\n"
#             result += f"    {bundle_var}.add_objects(prefetch_objs)\n"
#         else:
#             result += f"prefetch_objs = {win_artifact_var}.collect_prefetch_dir({args.prefetch_folder})\n"
#             result += f"{bundle_var}.add_objects(prefetch_objs)\n"

#         return auto_format(
#             result,
#             state,
#         )

#     @classmethod
#     def execute(
#         cls,
#         args: PrefetchModuleArgs,
#         config: NullConfig,
#         state: dict[str, Any],
#     ) -> None:
#         bundle = cls.get_akf_bundle(state)
#         if bundle is None:
#             logger.warning(
#                 "Executing PrefetchModule without a bundle won't do anything - skipping!"
#             )
#             return

#         # Check that a WindowsArtifactServiceAPI object is available. If it
#         # isn't, create a temporary context manager. (This, of course, requires
#         # that a machine is available with `akflib.machine`.)
#         close_win_artifact = False
#         if "akf_windows.artifacts.artifact_service" not in state:
#             hypervisor = cls.get_hypervisor(state)
#             if hypervisor is None:
#                 raise ValueError(
#                     "State variable `akflib.hypervisor` not available, can't determine IP"
#                 )

#             hypervisor = state["akflib.hypervisor"]
#             assert isinstance(hypervisor, HypervisorABC)

#             win_artifact = WindowsArtifactServiceAPI.auto_connect(
#                 hypervisor.get_maintenance_ip()
#             )

#             logger.info("Creating temporary WindowsArtifactServiceAPI object")
#             close_win_artifact = True
#         else:
#             win_artifact = state["akf_windows.artifacts.artifact_service"]
#             assert isinstance(win_artifact, WindowsArtifactServiceAPI)

#         prefetch_objs = win_artifact.collect_prefetch_dir(args.prefetch_folder)
#         if close_win_artifact:
#             win_artifact.rpyc_conn.close()
#             logger.info("Closed temporary WindowsArtifactServiceAPI object")

#         # Add all objects to the bundle
#         bundle.add_objects(prefetch_objs)
