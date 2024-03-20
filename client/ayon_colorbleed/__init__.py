import os

from ayon_core.addon import AYONAddon
from ayon_core.addon.interfaces import IPluginPaths


class ColorbleedAddon(AYONAddon, IPluginPaths):
    name = "colorbleed"

    def get_plugin_paths(self):
        """Implementation of IPluginPaths to get plugin paths."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        plugins_dir = os.path.join(current_dir, "plugins")

        return {
            "actions": [os.path.join(plugins_dir, "launcher_actions")],
            "load": [os.path.join(plugins_dir, "load")],
            "publish": [os.path.join(plugins_dir, "publish")]
        }
