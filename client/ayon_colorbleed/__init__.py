import os
import platform
import subprocess

import ayon_api
from ayon_core.addon import AYONAddon, click_wrap, ensure_addons_are_process_ready
from ayon_core.addon.interfaces import IPluginPaths


from .version import __version__


def _resolve_entity_uris(uris):
    """Resolve AYON Entity URIs to filepath

    Arguments:
        uris (list[str]): The AYON entity URIs.

    Returns:
        list[str]: The filepaths

    """
    response = ayon_api.post("resolve", resolveRoots=True, uris=uris)
    if response.status_code != 200:
        raise RuntimeError(
            f"Unable to resolve AYON entity URI: '{uris}'"
        )

    paths = []
    for entity in response.data["entities"]:
        paths.append(entity["filePath"])
    return paths


def resolve_entity_uri(entity_uri):
    if not entity_uri.startswith(("ayon://", "ayon+entity://")):
        # Assume not an entity URI
        return entity_uri
    return _resolve_entity_uris([entity_uri])


class ColorbleedAddon(AYONAddon, IPluginPaths):
    name = "colorbleed"
    title = "Colorbleed"
    version = __version__

    def get_plugin_paths(self):
        """Implementation of IPluginPaths to get plugin paths."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        plugins_dir = os.path.join(current_dir, "plugins")

        return {
            "actions": [os.path.join(plugins_dir, "launcher_actions")],
            "load": [os.path.join(plugins_dir, "load")],
            "publish": [os.path.join(plugins_dir, "publish")]
        }

    # region CLI
    def cli(self, addon_click_group):
        main_group = click_wrap.group(
            self._cli_main, name=self.name, help="Colorbleed addon"
        )
        (
            main_group.command(
                self._cli_run,
                name="run",
                help="Run filepaths"
            )
            .argument("paths", nargs=-1, required=True)
        )
        (
            main_group.command(
                self._cli_show_in_explorer,
                name="show-in-explorer",
                help="Show given paths or entity URIs in explorer."
            )
            .argument("paths", nargs=-1, required=True)
        )
        # Convert main command to click object and add it to parent group
        addon_click_group.add_command(
            main_group.to_click_obj()
        )

    def _cli_main(self):

        ensure_addons_are_process_ready(
            addon_name=self.name,
            addon_version=self.version
        )

    def _cli_run(
        self, paths
    ):
        """Run paths using OS default application"""
        print(f"Running: {paths}")
        for path in paths:
            path = resolve_entity_uri(path)
            self.run_file(path)

    def _cli_show_in_explorer(self, paths):
        """Open paths in system explorer"""
        print(f"Running show in explorer: {paths}")
        for path in paths:
            path = resolve_entity_uri(path)
            self.open_in_explorer(os.path.dirname(path))
    # endregion

    @staticmethod
    def run_file(path):
        platform_name = platform.system().lower()
        if platform_name == 'windows':  # Windows
            os.startfile(path)
        elif platform_name == 'darwin':  # macOS
            subprocess.Popen(('open', path))
        elif platform_name == "linux":  # linux variants
            subprocess.Popen(('xdg-open', path))
        else:
            raise RuntimeError(f"Unknown platform {platform.system()}")

    @staticmethod
    def open_in_explorer(path: str):
        platform_name = platform.system().lower()
        if platform_name == "windows":
            args = ["start", path]
        elif platform_name == "darwin":
            args = ["open", "-na", path]
        elif platform_name == "linux":
            args = ["xdg-open", path]
        else:
            raise RuntimeError(f"Unknown platform {platform.system()}")
        # Make sure path is converted correctly for 'os.system'
        os.system(subprocess.list2cmdline(args))
