"""
Base class for all API classes for the Windows agent.

This class should be subclassed by all API classes for the Windows agent. It
automatically connects to the base DispatchService as needed.
"""

from typing import Type, TypeVar

from akflib.core.agents.client import AKFServiceAPI

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
    @classmethod
    def auto_connect(cls: Type[T], host: str) -> T:
        """
        Automatically connect to the corresponding subservice, assuming that the
        `DispatchService` is running on the default port.
        """
        # Assumed port 18861
        with DispatchServiceAPI(host, 18861) as dispatch:
            # TODO: make this less flaky, use a property or classvar
            port = dispatch.start_service(cls.__name__.replace("API", ""))
            print(port)
            return cls(host, port)
