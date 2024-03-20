import pyblish.api
from ayon_core.lib import TextDef
from ayon_core.pipeline.publish import OpenPypePyblishPluginMixin


class CollectUserProductGroup(pyblish.api.InstancePlugin,
                             OpenPypePyblishPluginMixin):
    """Allow user to define `productGroup` on publish in new publisher"""

    order = pyblish.api.CollectorOrder + 0.499
    label = "Collect User Product Group"

    def process(self, instance):

        attr_values = self.get_attr_values_from_data(instance.data)
        user_product_group = attr_values.get("productGroup", "").strip()
        if not user_product_group:
            # Do nothing
            return

        if instance.data.get("productGroup"):
            self.log.warning(
                "User defined product group '{}' is not applied because "
                "publisher had already collected product group '{}'".format(
                    user_product_group,
                    instance.data["productGroup"]
                )
            )
            return

        self.log.debug("Setting product group: {}".format(user_product_group))
        instance.data["productGroup"] = user_product_group

    @classmethod
    def get_attribute_defs(cls):
        return [
            TextDef(
                "productGroup",
                label="Product Group",
                placeholder="User defined product group, e.g. 'Technical'",
                tooltip="User defined product group, e.g. 'Technical'."
                        " This does nothing when empty.",
                default=""
            )
        ]
