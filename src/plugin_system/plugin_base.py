"""
Base Plugin Class
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class BasePlugin(ABC):
    """Base class for all plugins"""

    def __init__(self, plugin_id: str, name: str, version: str = "1.0.0"):
        self.plugin_id = plugin_id
        self.name = name
        self.version = version
        self.is_enabled = False
        self.logger = logging.getLogger(f"{__name__}.{plugin_id}")

    @abstractmethod
    def initialize(self, config: Dict[str, Any] = None) -> bool:
        """
        Initialize the plugin

        Args:
            config: Configuration dictionary for the plugin

        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the plugin's main functionality

        Args:
            input_data: Input data for the plugin

        Returns:
            Dict[str, Any]: Result of the plugin execution
        """
        pass

    @abstractmethod
    def shutdown(self) -> bool:
        """
        Shutdown the plugin and clean up resources

        Returns:
            bool: True if shutdown successful, False otherwise
        """
        pass

    def enable(self):
        """Enable the plugin"""
        self.is_enabled = True
        self.logger.info(f"Plugin {self.name} enabled")

    def disable(self):
        """Disable the plugin"""
        self.is_enabled = False
        self.logger.info(f"Plugin {self.name} disabled")

    def get_info(self) -> Dict[str, Any]:
        """
        Get plugin information

        Returns:
            Dict[str, Any]: Plugin information
        """
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "enabled": self.is_enabled
        }