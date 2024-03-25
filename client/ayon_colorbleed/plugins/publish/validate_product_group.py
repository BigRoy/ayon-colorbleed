import pyblish.api

from ayon_core.pipeline.publish import OpenPypePyblishPluginMixin
from ayon_api import get_product_by_name


class ValidateProductGroupChange(pyblish.api.InstancePlugin,
                                OpenPypePyblishPluginMixin):
    """Log a warning if `productGroup` changes from current product's group"""

    order = pyblish.api.ValidatorOrder
    label = "Validate Product Group Change"

    def process(self, instance):

        if not instance.data.get("productGroup"):
            return

        product_group = instance.data["productGroup"]
        self.log.debug(
            "Instance has product group set to: {}".format(product_group)
        )

        asset_doc = instance.data.get("assetEntity")
        if not asset_doc:
            return

        product_name = instance.data.get("productName")
        if not product_name:
            return

        # Get existing product if it exists
        project_name = instance.context.data["projectName"]
        existing_product_doc = get_product_by_name(
            project_name, product_name, asset_doc["_id"],
            fields=["data.productGroup"]
        )
        if not existing_product_doc:
            return

        existing_group = existing_product_doc.get("data", {}).get("productGroup")
        if not existing_group:
            return

        if existing_group != product_group:
            self.log.warning(
                "Product group changes from `{}` to `{}`".format(
                    existing_group, product_group
                )
            )
