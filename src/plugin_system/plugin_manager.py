"""
Plugin Manager for loading, managing, and executing plugins
"""

import os
import importlib
import inspect
from typing import Dict, Any, List, Optional, Type
import logging

from .plugin_base import BasePlugin

logger = logging.getLogger(__name__)


class PluginManager:
    """Manages the lifecycle of plugins"""

    def __init__(self, plugins_dir: str = "./plugins"):
        self.plugins_dir = plugins_dir
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_classes: Dict[str, Type[BasePlugin]] = {}

        # Ensure the plugins directory exists
        os.makedirs(self.plugins_dir, exist_ok=True)

    def discover_plugins(self) -> List[str]:
        """
        Discover available plugins in the plugins directory

        Returns:
            List of plugin module names
        """
        plugin_modules = []

        if not os.path.exists(self.plugins_dir):
            logger.warning(f"Plugins directory {self.plugins_dir} does not exist")
            return plugin_modules

        for item in os.listdir(self.plugins_dir):
            item_path = os.path.join(self.plugins_dir, item)
            if os.path.isdir(item_path):
                # Check if it's a Python package (has __init__.py)
                init_file = os.path.join(item_path, "__init__.py")
                if os.path.exists(init_file):
                    plugin_modules.append(item)
            elif item.endswith(".py") and item != "__init__.py":
                # Single file plugin
                plugin_modules.append(item[:-3])  # Remove .py extension

        logger.info(f"Discovered plugins: {plugin_modules}")
        return plugin_modules

    def load_plugin(self, plugin_name: str) -> bool:
        """
        Load a plugin by name

        Args:
            plugin_name: Name of the plugin to load

        Returns:
            bool: True if plugin loaded successfully, False otherwise
        """
        try:
            # Try to import the plugin module
            if os.path.exists(os.path.join(self.plugins_dir, f"{plugin_name}.py")):
                # Single file plugin
                module_name = f"plugins.{plugin_name}"
                module = importlib.import_module(module_name)
            else:
                # Package plugin
                module_name = f"plugins.{plugin_name}.plugin"
                module = importlib.import_module(module_name)

            # Find plugin classes in the module
            plugin_classes = []
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and
                    issubclass(obj, BasePlugin) and
                    obj != BasePlugin):
                    plugin_classes.append(obj)

            if not plugin_classes:
                logger.error(f"No plugin class found in module {module_name}")
                return False

            # Use the first plugin class found (could be extended to handle multiple)
            plugin_class = plugin_classes[0]

            # Instantiate the plugin
            plugin_instance = plugin_class()
            plugin_id = plugin_instance.plugin_id

            # Store the plugin class and instance
            self.plugin_classes[plugin_id] = plugin_class
            self.plugins[plugin_id] = plugin_instance

            logger.info(f"Loaded plugin: {plugin_instance.name} (ID: {plugin_id})")
            return True

        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {str(e)}")
            return False

    def load_all_plugins(self) -> Dict[str, bool]:
        """
        Load all discovered plugins

        Returns:
            Dictionary mapping plugin names to load success status
        """
        results = {}
        plugin_names = self.discover_plugins()

        for plugin_name in plugin_names:
            results[plugin_name] = self.load_plugin(plugin_name)

        return results

    def get_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        """
        Get a plugin by its ID

        Args:
            plugin_id: ID of the plugin

        Returns:
            The plugin instance if found, None otherwise
        """
        return self.plugins.get(plugin_id)

    def get_plugin_by_name(self, name: str) -> Optional[BasePlugin]:
        """
        Get a plugin by its name

        Args:
            name: Name of the plugin

        Returns:
            The plugin instance if found, None otherwise
        """
        for plugin in self.plugins.values():
            if plugin.name == name:
                return plugin
        return None

    def list_plugins(self) -> List[Dict[str, Any]]:
        """
        List all loaded plugins

        Returns:
            List of plugin information dictionaries
        """
        return [plugin.get_info() for plugin in self.plugins.values()]

    def enable_plugin(self, plugin_id: str) -> bool:
        """
        Enable a plugin

        Args:
            plugin_id: ID of the plugin to enable

        Returns:
            bool: True if plugin enabled successfully, False otherwise
        """
        plugin = self.get_plugin(plugin_id)
        if plugin is None:
            return False

        if not plugin.is_enabled:
            plugin.enable()
        return True

    def disable_plugin(self, plugin_id: str) -> bool:
        """
        Disable a plugin

        Args:
            plugin_id: ID of the plugin to disable

        Returns:
            bool: True if plugin disabled successfully, False otherwise
        """
        plugin = self.get_plugin(plugin_id)
        if plugin is None:
            return False

        if plugin.is_enabled:
            plugin.disable()
        return True

    def execute_plugin(self, plugin_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a plugin

        Args:
            plugin_id: ID of the plugin to execute
            input_data: Input data for the plugin

        Returns:
            Result of the plugin execution
        """
        plugin = self.get_plugin(plugin_id)
        if plugin is None:
            return {
                "success": False,
                "error": f"Plugin {plugin_id} not found"
            }

        if not plugin.is_enabled:
            return {
                "success": False,
                "error": f"Plugin {plugin_id} is not enabled"
            }

        try:
            result = plugin.execute(input_data)
            return {
                "success": True,
                "plugin_id": plugin_id,
                "plugin_name": plugin.name,
                "result": result
            }
        except Exception as e:
            self.logger.error(f"Error executing plugin {plugin_id}: {str(e)}")
            return {
                "success": False,
                "plugin_id": plugin_id,
                "error": str(e)
            }

    def initialize_plugin(self, plugin_id: str, config: Dict[str, Any] = None) -> bool:
        """
        Initialize a plugin

        Args:
            plugin_id: ID of the plugin to initialize
            config: Configuration for the plugin

        Returns:
            bool: True if initialization successful, False otherwise
        """
        plugin = self.get_plugin(plugin_id)
        if plugin is None:
            return False

        try:
            success = plugin.initialize(config)
            if success:
                plugin.enable()
            return success
        except Exception as e:
            self.logger.error(f"Error initializing plugin {plugin_id}: {str(e)}")
            return False

    def shutdown_plugin(self, plugin_id: str) -> bool:
        """
        Shutdown a plugin

        Args:
            plugin_id: ID of the plugin to shutdown

        Returns:
            bool: True if shutdown successful, False otherwise
        """
        plugin = self.get_plugin(plugin_id)
        if plugin is None:
            return False

        try:
            success = plugin.shutdown()
            if success:
                plugin.disable()
            return success
        except Exception as e:
            self.logger.error(f"Error shutting down plugin {plugin_id}: {str(e)}")
            return False

    def shutdown_all(self):
        """Shutdown all loaded plugins"""
        for plugin_id in list(self.plugins.keys()):
            self.shutdown_plugin(plugin_id)