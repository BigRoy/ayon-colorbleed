import os

from ayon_core.lib import is_running_from_build
from ayon_core.pipeline import load


class CopyRepresentationId(load.LoaderPlugin):
    """Debug context data of representation"""

    product_types = {"*"}
    representations = {"*"}

    enabled = (
        not is_running_from_build() or
        os.getenv("AYON_USE_DEV") == "1"
    )

    label = "Copy representation id"
    order = 9999
    icon = "bug"
    color = "gray"

    def load(self, context, name, namespace, data):

        from qtpy import QtWidgets

        value = context["representation"]["id"]

        # Log it
        self.log.info(value)

        # Copy to clipboard
        clipboard = QtWidgets.QApplication.clipboard()
        assert clipboard, "Must have running QApplication instance"
        clipboard.setText(value)
