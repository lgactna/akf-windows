"""
Base class for all API classes for the Windows agent.

This class should be subclassed by all API classes for the Windows agent. It
automatically connects to the base DispatchService as needed.
"""

import logging
from typing import ClassVar, Type, TypeVar

from akflib.core.agents.client import AKFServiceAPI

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="WindowsServiceAPI")


class DispatchServiceAPI(AKFServiceAPI):
    def start_service(self, service_name: str) -> int:
        """
        Start a service by name. Return the port number allocated for the service.
        """
        return self.rpyc_conn.root.start_service(service_name)  # type: ignore[no-any-return]

    def stop_service(self, service_name: str) -> None:
        """
        Stop a service by name.
        """
        self.rpyc_conn.root.stop_service(service_name)

    def get_service_port(self, service_name: str) -> int:
        """
        Get the port number for a service by name.
        """
        return self.rpyc_conn.root.get_service_port(service_name)  # type: ignore[no-any-return]

    def get_available_services(self) -> list[str]:
        """
        Get a list of available services that can be started.
        """
        return self.rpyc_conn.root.get_available_services()  # type: ignore[no-any-return]

    def get_running_services(self) -> dict[str, int]:
        """
        Get a dictionary of running services and their port numbers.
        """
        return self.rpyc_conn.root.get_running_services()  # type: ignore[no-any-return]


class WindowsServiceAPI(AKFServiceAPI):
    # The name of the related subservice class.
    related_service: ClassVar[str]

    def __init_subclass__(cls) -> None:
        """
        Check that subclasses have a related service declared.
        """
        super().__init_subclass__()

        if not hasattr(cls, "related_service"):
            raise TypeError(
                f"Can't instantiate abstract class {cls.__name__} "
                f"without required attribute 'related_service'"
            )

    @classmethod
    def auto_connect(
        cls: Type[T], host: str, port: int = 18861, wait_until_ready: bool = True
    ) -> T:
        """
        Automatically connect to the corresponding subservice, assuming that the
        `DispatchService` is running on the default port.

        :param host: The host to connect to.
        :param port: The port to connect to. The default port is 18861, and should
            be used in nearly all cases.
        :param wait_until_ready: If True, wait indefinitely until the port is
            available.
        :return: An instance of the service API class.
        """
        # If a timeout is specified, wait until the dispatch service port is
        # available.
        #
        # Attempting to connect to the agent as soon as the Guest Additions
        # runlevel is "desktop" may sometimes fail, as the agent needs some time
        # to get started.

        # Assumed port 18861
        while True:
            try:
                logger.info(
                    f"Attempting to connect to the dispatch service at {host}:{port}"
                )
                with DispatchServiceAPI(host, port) as dispatch:
                    port = dispatch.start_service(cls.related_service)
                    logger.info(f"{cls.related_service} is running on port {port}")
                    return cls(host, port)
            except TimeoutError:
                if not wait_until_ready:
                    raise TimeoutError("Dispatch service timed out")

                logger.info("Dispatch service timed out, trying again")
