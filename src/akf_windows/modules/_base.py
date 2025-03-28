"""
Various frequently-reused utility functions.
"""

import logging
from typing import Any, ClassVar, Type

from akflib.declarative.core import AKFModule, NullArgs, NullConfig
from akflib.declarative.util import auto_format

from akf_windows.api._base import WindowsServiceAPI

logger = logging.getLogger(__name__)


class ServiceModule(AKFModule[NullArgs, NullConfig]):
    """
    Base class for modules that create or manage simple service API objects.

    Removes a lot of the boilerplate. Just specify your aliases, dependencies, and the
    name of the state variable you want to use.

    This creates a new variable for your related AKFServiceAPI object. It does
    not generate a context manager.
    """

    arg_model = NullArgs
    config_model = NullConfig

    aliases: ClassVar[list[str]]
    dependencies: ClassVar[set[str]]

    state_var: ClassVar[str]
    service_api_class: ClassVar[Type[WindowsServiceAPI]]
    service_api_var_name: ClassVar[str]

    def __init_subclass__(cls) -> None:
        """
        Check that subclasses have required attributes.
        """
        super().__init_subclass__()

        REQUIRED_ATTRIBUTES = ["state_var", "service_api_class", "service_api_var_name"]
        cls.check_required_attributes(cls, REQUIRED_ATTRIBUTES)

    @classmethod
    def api_name(cls) -> str:
        return cls.service_api_class.__name__


class ServiceStartModule(ServiceModule):
    """
    Generalized class for creating a new service API object/variable.

    If creating your service API object is as simple as creating an RPyC connection
    and adding it to the state dictionary, this class will handle that for you.
    """

    aliases: ClassVar[list[str]]
    dependencies: ClassVar[set[str]]

    state_var: ClassVar[str]
    service_api_class: ClassVar[Type[WindowsServiceAPI]]
    service_api_var_name: ClassVar[str]

    @classmethod
    def generate_code(
        cls, args: NullArgs, config: NullConfig, state: dict[str, Any]
    ) -> str:
        if cls.state_var in state:
            logger.warning(f"{cls.api_name()} object already exists, skipping")
            return ""

        # Set new state variables
        state[cls.state_var] = cls.service_api_var_name

        # Build line
        hypervisor_var = cls.get_hypervisor_var(state)
        if hypervisor_var is None:
            raise ValueError(
                "State variable `akflib.hypervisor_var` not available, can't determine IP for auto_connect"
            )
        return auto_format(
            f"{cls.service_api_var_name} = {cls.api_name()}.auto_connect({hypervisor_var}.get_maintenance_ip())",
            state,
        )

    @classmethod
    def execute(
        cls,
        args: NullArgs,
        config: NullConfig,
        state: dict[str, Any],
    ) -> None:
        if cls.state_var in state:
            logger.warning(f"{cls.api_name()} object already exists, skipping")
            return

        hypervisor = cls.get_hypervisor(state)
        if hypervisor is None:
            raise ValueError(
                "State variable `akflib.hypervisor` not available, can't determine IP for auto_connect"
            )

        win_artifact = cls.service_api_class.auto_connect(
            hypervisor.get_maintenance_ip()
        )

        state[cls.state_var] = win_artifact


class ServiceStopModule(ServiceModule):
    """
    Generalized class for destroying existing service API objects.
    """

    aliases: ClassVar[list[str]]
    dependencies: ClassVar[set[str]]

    state_var: ClassVar[str]
    service_api_class: ClassVar[Type[WindowsServiceAPI]]
    service_api_var_name: ClassVar[str]

    @classmethod
    def generate_code(
        cls, args: NullArgs, config: NullConfig, state: dict[str, Any]
    ) -> str:
        if cls.state_var not in state:
            logger.warning(f"{cls.api_name()} object does not exist, skipping")
            return ""

        del state[cls.state_var]
        return auto_format(f"{cls.service_api_var_name}.rpyc_conn.close()", state)

    @classmethod
    def execute(
        cls,
        args: NullArgs,
        config: NullConfig,
        state: dict[str, Any],
    ) -> None:
        if cls.state_var not in state:
            logger.warning(f"{cls.api_name()} object does not exist, skipping")
            return

        service_api = state[cls.state_var]
        assert isinstance(service_api, WindowsServiceAPI)
        service_api.rpyc_conn.close()

        del state[cls.state_var]
        logger.info(f"Deleted {cls.api_name()} object")
