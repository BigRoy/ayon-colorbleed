import os
import json

from ayon_core.lib import is_running_from_build
from ayon_core.pipeline import load
from ayon_core.style import load_stylesheet


class ShowContextData(load.LoaderPlugin):
    """Debug context data of representation"""

    product_types = {"*"}
    representations = ["*"]

    enabled = (
        not is_running_from_build() or
        os.getenv("AYON_USE_DEV") == "1"
    )

    label = "Show Context Data"
    order = 9999
    icon = "bug"
    color = "gray"

    def load(self, context, name, namespace, data):

        from qtpy import QtWidgets

        json_str = json.dumps(context,
                              default=str,
                              indent=4,
                              sort_keys=True)

        # Log it
        self.log.info(json_str)

        # Copy to clipboard
        clipboard = QtWidgets.QApplication.clipboard()
        assert clipboard, "Must have running QApplication instance"
        clipboard.setText(json_str)

        # Show in UI
        global edit
        edit = QtWidgets.QPlainTextEdit()
        edit.setWindowTitle(
            "Context data for: "
            "{0[project][name]} > "
            "{0[asset][name]} > "
            "{0[subset][name]} > "
            "v{0[version][name]:03d} > "
            "{0[representation][name]}".format(context)
        )
        edit.insertPlainText(json_str)
        edit.resize(800, 500)
        edit.setStyleSheet(load_stylesheet())
        edit.show()
