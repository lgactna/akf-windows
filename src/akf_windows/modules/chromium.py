"""
Declarative modules for interacting with Chromium browsers.
"""

import logging
import random
import time
from pathlib import Path
from typing import Any, ClassVar, Literal

from akflib.core.hypervisor.base import HypervisorABC
from akflib.declarative.core import AKFModule, AKFModuleArgs, NullConfig
from akflib.declarative.util import auto_format

from akf_windows.api.chromium import ChromiumServiceAPI
from akf_windows.modules._base import ServiceStartModule, ServiceStopModule

logger = logging.getLogger(__name__)


class ChromiumServiceStartModule(ServiceStartModule):
    """
    Create a persistent ChromiumServiceAPI object.

    State variables:
    - akflib.hypervisor (read): to get the IP of the currently active virtual machine.
    - akf_windows.chromium.chromium_service (write): Set to the name of the
      ChromiumServiceAPI variable on generation; set to an instance of
      ChromiumServiceAPI on execution.
    """

    aliases = ["chromium_service_start"]

    dependencies: ClassVar[set[str]] = {"akf_windows.api.chromium.ChromiumServiceAPI"}

    state_var = "akf_windows.chromium.chromium_service"
    service_api_class = ChromiumServiceAPI
    service_api_var_name = "chromium_service"


class ChromiumServiceStopModule(ServiceStopModule):
    """
    Close a persistent ChromiumServiceAPI object.

    State variables:
    - akf_windows.chromium.chromium_service (read/write): Closed and/or
      cleared from state.
    """

    aliases = ["chromium_service_stop"]

    dependencies: ClassVar[set[str]] = {"akf_windows.api.chromium.ChromiumServiceAPI"}

    state_var = "akf_windows.chromium.chromium_service"
    service_api_class = ChromiumServiceAPI
    service_api_var_name = "chromium_service"
    

class ChromiumVisitURLsModuleArgs(AKFModuleArgs):
    browser: Literal["msedge", "chrome"] = "msedge"
    
    # A list of URLs to visit, in order.
    urls: list[str] = []
    
    # A file to load `urls` from, as a newline-separated list.
    file: Path | None = None
    
    # The time to wait between each URL visit, in seconds.
    wait_time: int = 5
    
    # Jitter between each URL visit, as an absolute value. A jitter of 1 means
    # that the wait time will be between 4 and 6 seconds, if wait_time is 5.
    # The wait time will never be less than 1 second.
    jitter: int = 0

class ChromiumVisitURLsModule(AKFModule[ChromiumVisitURLsModuleArgs, NullConfig]):
    """
    Visit a list of URLs in a Chromium browser.

    State variables:
    - akf_windows.artifacts.chromium_service (read): to get the IP of the currently active virtual machine.
    """

    aliases = ["chromium_visit_urls"]
    arg_model = ChromiumVisitURLsModuleArgs
    config_model = NullConfig

    dependencies: ClassVar[set[str]] = {"akf_windows.api.chromium.ChromiumServiceAPI", "time", "random", "pathlib.Path"}

    @classmethod
    def generate_code(
        cls, args: ChromiumVisitURLsModuleArgs, config: NullConfig, state: dict[str, Any]
    ) -> str:
        # Exactly one of `urls` or `file` must be provided.
        if not(bool(args.urls) ^ bool(args.file)):
            raise ValueError("Exactly one of `urls` or `file` must be provided.")

        result = ""

        # If `file` is provided, then load its contents into a variable called `urls`.
        # If `urls` is provided, then use it to construct a list variable in-place.
        if args.file:
            result += f'url_path = Path("{args.file.as_posix()}")\n'
            result += 'if not url_path.exists():\n'
            result += f'    raise FileNotFoundError(f"File {args.file} does not exist.")\n'
            result += 'if not url_path.is_file():\n'
            result += f'    raise ValueError(f"{args.file} is not a file.")\n'
            result += 'if url_path.stat().st_size == 0:\n'
            result += f'    raise ValueError(f"{args.file} is empty.")\n'
            result += "\n"
            result += 'with open(url_path, "rt") as f:\n'
            result += '    urls = [line.strip() for line in f.readlines()]'
        else:
            result += "urls = [\n"
            for url in args.urls:
                result += f'    "{url}",\n'
            result += "]\n"
        
        result += "\n"
            
        # The variable for the service is `chromium_service` regardless of whether
        # it currently exists or not. If it doens't exist, we'll wrap the entire
        # thing in a context manager and indent after the fact.
        if args.browser == "msedge":
            result += "chromium_service.kill_edge()\n"
        result += f'chromium_service.set_browser("{args.browser}")\n'
        result += "page = chromium_service.browser.new_page()\n"
        result += "\n"
        result += "for url in urls:\n"
        result += "    page.goto(url)\n"
        result += f"    time.sleep({args.wait_time} + random.randint(-{args.jitter}, {args.jitter}))\n"
        
        if "akf_windows.chromium.chromium_service" not in state:
            hypervisor_var = cls.get_hypervisor_var(state)
            if hypervisor_var is None:
                raise ValueError(
                    "State variable `akflib.hypervisor` not available, can't determine IP"
                )
            
            # Temporarily kick up indent
            state['indentation_level'] += 1
            result = auto_format(result, state)
            state['indentation_level'] -= 1
            result = f"with ChromiumServiceAPI.auto_connect({hypervisor_var}.get_maintenance_ip()) as chromium_service:\n" + result

        return auto_format(result, state)
    
    @classmethod
    def execute(
        cls, args: ChromiumVisitURLsModuleArgs, config: NullConfig, state: dict[str, Any]
    ) -> None:
        """
        Execute the module.

        Args:
            args (ChromiumVisitURLsModuleArgs): The module arguments.
            config (NullConfig): The module configuration.
            state (dict[str, Any]): The module state.

        Raises:
            NotImplementedError: This method is not implemented yet.
        """
        # Exactly one of `urls` or `file` must be provided.
        if not (bool(args.urls) ^ bool(args.file)):
            raise ValueError("Exactly one of `urls` or `file` must be provided.")
        
        # If `file` is provided, check that it exists; if it exists, load each
        # line into `urls`.
        if args.file:
            if not args.file.exists():
                raise FileNotFoundError(f"File {args.file} does not exist.")
            if not args.file.is_file():
                raise ValueError(f"{args.file} is not a file.")
            if args.file.stat().st_size == 0:
                raise ValueError(f"{args.file} is empty.")
            
            with open(args.file, "rt") as f:
                args.urls = [line.strip() for line in f.readlines()]
                
        # Check that a ChromiumServiceAPI object is available. If it isn't,
        # create a temporary context manager.
        close_chromium_service = False
        if "akf_windows.chromium.chromium_service" not in state:
            hypervisor = cls.get_hypervisor(state)
            if hypervisor is None:
                raise ValueError(
                    "State variable `akflib.hypervisor` not available, can't determine IP"
                )

            hypervisor = state["akflib.hypervisor"]
            assert isinstance(hypervisor, HypervisorABC)

            logger.info("Creating temporary ChromiumServiceAPI object")
            chromium_service = ChromiumServiceAPI.auto_connect(
                hypervisor.get_maintenance_ip()
            )
            close_chromium_service = True
        else:
            chromium_service = state["akf_windows.chromium.chromium_service"]
            assert isinstance(chromium_service, ChromiumServiceAPI)
            
        # Visit the URLs.
        if args.browser == "msedge":
            logger.info("Killing existing Edge processes")
            chromium_service.kill_edge()
        
        chromium_service.set_browser(args.browser)
        logger.info(f"Opening {args.browser=}")
        page = chromium_service.browser.new_page()
        
        for url in args.urls:
            logger.info(f"Visiting {url}")
            page.goto(url)
            time.sleep(args.wait_time + random.randint(-args.jitter, args.jitter))
            
        if close_chromium_service:
            chromium_service.rpyc_conn.close()
            logger.info("Closed temporary ChromiumServiceAPI object")
            
class ChromiumHistoryModule():
    pass