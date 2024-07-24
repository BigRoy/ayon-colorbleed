from typing import List

import pyblish.api
from ayon_core.lib import EnumDef
from ayon_core.pipeline.publish import AYONPyblishPluginMixin
from ayon_core.pipeline import get_current_project_name
from ayon_api import get_project


def get_project_status_names(project_entity: dict) -> List[str]:
    """Return available status names in current project"""
    statuses = project_entity["statuses"]
    return [status["name"] for status in statuses]


class SetVersionStatus(pyblish.api.InstancePlugin, AYONPyblishPluginMixin):
    """Allow user to set status of the to be published version."""

    order = pyblish.api.IntegratorOrder - 0.1
    label = "Set Status"

    statuses: List[str] = [{"value": None, "label": "Unknown"}]

    @classmethod
    def apply_settings(cls, project_settings):
        project_name = get_current_project_name()
        project = get_project(project_name)
        cls.statuses = get_project_status_names(project)

    def process(self, instance):
        attr_values = self.get_attr_values_from_data(instance.data)
        status = attr_values.get("status")
        if not status:
            return

        existing_status = instance.data.get("status")
        if existing_status:
            # Already configured
            self.log.debug(
                "Skipping setting of status because instance 'status' "
                f"data is already set to: {existing_status}")
            return

        self.log.info(f"Setting status to: {status}")
        instance.data["status"] = status

    @classmethod
    def get_attribute_defs(cls):
        return [
            EnumDef(
                "status",
                label="Set version status",
                items=cls.statuses,
                default=cls.statuses[0]
            )
        ]
