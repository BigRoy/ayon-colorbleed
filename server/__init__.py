from typing import Type, TYPE_CHECKING

from nxtools import logging
from ayon_server.actions import SimpleActionManifest
from ayon_server.addons import BaseServerAddon

from .settings import ColorbleedSettings, DEFAULT_VALUES

if TYPE_CHECKING:
    from ayon_server.actions import ActionExecutor, ExecuteResponseModel


class ColorbleedAddon(BaseServerAddon):
    settings_model: Type[ColorbleedSettings] = ColorbleedSettings

    async def get_default_settings(self):
        settings_model_cls = self.get_settings_model()
        return settings_model_cls(**DEFAULT_VALUES)

    async def get_simple_actions(
        self,
        project_name: str | None = None,
        variant: str = "production",
    ) -> list[SimpleActionManifest]:
        return [
            SimpleActionManifest(
                identifier="colorbleed.open_file",
                label="Open file",
                category="Colorbleed",
                order=100,
                icon={
                    "type": "material-symbols",
                    "name": "live_tv",
                    "color": "#FFA500"
                },
                entity_type="version",
                entity_subtypes=None,
                allow_multiselection=False,
            ),
            SimpleActionManifest(
                identifier="colorbleed.show_in_explorer",
                label="Show in explorer",
                category="Colorbleed",
                order=100,
                icon={
                    "type": "material-symbols",
                    "name": "folder_open",
                    "color": "#FFA500"
                },
                entity_type="version",
                entity_subtypes=None,
                allow_multiselection=False,
            )
        ]

    async def execute_action(
        self,
        executor: "ActionExecutor",
    ) -> "ExecuteResponseModel":
        """Execute an action provided by the addon"""
        logging.debug(f"Executing ayon-colorbleed action: {executor.context}")
        context = executor.context
        if not context.entity_type:
            return await executor.get_server_action_response(
                success=True,
                message=f"No entity type in context: {context}"
            )
        if executor.identifier == "colorbleed.show_in_explorer":
            return await executor.get_launcher_action_response(
                args=[
                    "addon", "colorbleed", "show-in-explorer",
                    "--project", context.project_name,
                    "--entity_type", context.entity_type,
                    *context.entity_ids
                ]
            )
        elif executor.identifier == "colorbleed.open_file":
            return await executor.get_launcher_action_response(
                args=[
                    "addon", "colorbleed", "run",
                    "--project", context.project_name,
                    "--entity_type", context.entity_type,
                    *context.entity_ids
                ]
            )
