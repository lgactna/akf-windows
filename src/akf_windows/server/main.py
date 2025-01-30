"""
The Windows agent entrypoint, implemented as a single RPyC service (that is not
a subclass of `AKFService`).

This module's primary goal is to report on available services and instantiate or
terminate them when requested. This helps manage resources and ensure that only
the necessary services are running at any given time.
"""

import logging
import multiprocessing as mp
import sys
from dataclasses import dataclass
from typing import ClassVar

import rpyc
from rpyc.utils.server import ThreadedServer

from akf_windows.server.chromium import ChromiumService

# Set up logging
logging.basicConfig(
    handlers=[logging.StreamHandler(sys.stdout)],
    level=logging.INFO,
    format="%(filename)s:%(lineno)d | %(asctime)s | [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger()

# TODO: this can be automatically built at runtime
AVAILABLE_SERVICES = {
    "ChromiumService": ChromiumService,
}


def start_subservice(server: rpyc.ThreadedServer) -> None:
    """
    Entrypoint for starting a new ThreadedServer for a given service.

    This should be called from a new process each time.
    """
    # Don't know if there's any other setup that needs to happen here, but this
    # is its own function for now

    # Blocking.
    server.start()


@dataclass
class ServiceInfo:
    """
    Information about a server and its status.
    """

    process: mp.Process
    server: rpyc.ThreadedServer
    port: int


# ignore: mypy does not recognize the `rpyc.Service` class
class DispatchService(rpyc.Service):  # type: ignore[misc]
    """
    The "main" service that serves as the dispatch mechanism for agent subservices.
    """

    running_services: ClassVar[dict[str, ServiceInfo]] = {}

    def exposed_start_service(self, service_name: str) -> int:
        """
        Start a service by name. Return the port number allocated for the service.
        """
        # Check if service exists
        if service_name not in AVAILABLE_SERVICES:
            raise ValueError(f"Service {service_name} not found.")

        # Check if service is already running, in which case just return the exists
        # port number
        if service_name in self.running_services:
            return self.running_services[service_name].port

        service_class = AVAILABLE_SERVICES[service_name]
        server = ThreadedServer(
            service_class, port=0, protocol_config={"allow_all_attrs": True}
        )

        # Start the service in a new process
        process = mp.Process(target=start_subservice, args=(server,))
        process.start()

        port = server.port
        logger.info(f"Started service {service_name} on port {port}")
        # TODO: does two processes having a handle to the same service do
        # what i expected it to do?
        self.running_services[service_name] = ServiceInfo(process, server, port)

        return port

    def exposed_stop_service(self, service_name: str) -> None:
        """
        Stop a service by name.
        """
        if service_name not in self.running_services:
            raise ValueError(f"Service {service_name} not found.")

        logger.info(f"Stopping service {service_name}")
        service_info = self.running_services.pop(service_name)
        service_info.process.terminate()
        service_info.server.close()

    def exposed_get_available_services(self) -> list[str]:
        """
        Get a list of available services that can be started.
        """
        return list(AVAILABLE_SERVICES.keys())

    def exposed_get_running_services(self) -> dict[str, int]:
        """
        Get a dictionary of running services and their corresponding ports.
        """
        return {k: v.port for k, v in self.running_services.items()}


def main() -> None:
    # Bind the server to the standard port.
    server = ThreadedServer(
        DispatchService, port=18861, protocol_config={"allow_all_attrs": True}
    )
    logger.info("Starting Windows agent service on port 18861")
    server.start()
    
    # Teardown - the server has terminated and all subprocesses should be killed
    logger.info("DispatchService received interrupt, tearing down services")
    service: DispatchService = server.service
    for subservice in service.running_services.values():
        logger.info(f"Killing process with PID {subservice.process.pid}")
        subservice.process.kill()
