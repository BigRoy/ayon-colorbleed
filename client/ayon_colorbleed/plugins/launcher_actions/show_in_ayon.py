import os
import webbrowser

from ayon_core.pipeline import LauncherAction
from ayon_core.resources import get_ayon_icon_filepath


class ShowInAyon(LauncherAction):
    """Open AYON browser page to the current context."""
    name = "showinayon"
    label = "Show in AYON"
    icon = get_ayon_icon_filepath()
    color = "#e0e1e1"
    order = 999

    def process(self, selection, **kwargs):

        url = os.environ["AYON_SERVER_URL"]
        if selection.is_project_selected:
            project_name = selection.project_name
            url += f"/projects/{project_name}/browser"

        # TODO: Implement support to directly browse to a folder and task once
        #   the ayon frontend supports that

        # Open URL in webbrowser
        self.log.info(f"Opening URL: {url}")
        webbrowser.open(url,
                        # Try in new tab
                        new=2)
