import subprocess

from ayon_core.pipeline import LauncherAction
from ayon_core.lib import is_dev_mode_enabled


class LaunchPublishReportViewer(LauncherAction):
    """Launch AYON Publish Report Viewer."""
    name = "publishreportviewer"
    label = "Report Viewer"
    icon = {
        "type": "awesome-font",
        "name": "fa.bug",
        "color": "#666699"
    }
    order = 999999

    def is_compatible(self, selection):
        # Show only in DEV mode
        if is_dev_mode_enabled():
            return True

    def process(self, selection, **kwargs):
        from ayon_core.lib.execute import get_ayon_launcher_args

        args = get_ayon_launcher_args(
            "publish-report-viewer", "--debug"
        )
        subprocess.Popen(args)
