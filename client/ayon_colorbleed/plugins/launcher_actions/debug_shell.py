import typing
import os
import subprocess

from ayon_core.pipeline import LauncherAction
from ayon_api import get_project

if typing.TYPE_CHECKING:
    from typing import Optional
    from qtpy import QtGui
    from ayon_core.lib.applications import Application


def get_application_qt_icon(
        application: "Application"
) -> "Optional[QtGui.QIcon]":
    """Get the Q"""
    # TODO: Improve workflow to get the icon, remove 'color' hack
    from ayon_core.tools.launcher.models.actions import get_action_icon
    from ayon_core.tools.utils.lib import get_qt_icon
    application.color = "white"
    return get_qt_icon(get_action_icon(application))


class DebugShell(LauncherAction):
    """Run any host environment in command line."""
    name = "debugshell"
    label = "Shell"
    icon = "terminal"
    color = "#e8770e"
    order = 10

    def is_compatible(self, session):
        required = {"AYON_PROJECT_NAME", "AYON_FOLDER_PATH", "AYON_TASK_NAME"}
        return all(session.get(key) for key in required)

    def process(self, session, **kwargs):
        from ayon_core.lib.applications import get_app_environments_for_context
        from qtpy import QtGui

        # Get cursor position directly so the menu shows closer to where user
        # clicked because the get applications logic might take a brief moment
        pos = QtGui.QCursor.pos()

        # Get the environment
        project = session["AYON_PROJECT_NAME"]
        folder_path = session["AYON_FOLDER_PATH"]
        task = session["AYON_TASK_NAME"]

        applications = self.get_applications(project)
        result = self.choose_app(applications, pos)
        if not result:
            return

        app_name, app = result
        print(f"Retrieving environment for: {app_name}..")
        env = get_app_environments_for_context(project,
                                               folder_path,
                                               task,
                                               app_name)

        # If an executable is found. Then add the parent folder to PATH
        # just so we can run the application easily from the command line.
        exe = app.find_executable()
        if exe:
            exe_path = exe._realpath()
            folder = os.path.dirname(exe_path)
            print(f"Appending to PATH: {folder}")
            env["PATH"] += os.pathsep + folder

        cwd = env.get("AYON_WORKDIR")
        if cwd:
            print(f"Setting Work Directory: {cwd}")

        print(f"Launch cmd in environment of {app_name}..")
        subprocess.Popen("cmd",
                         env=env,
                         cwd=cwd,
                         creationflags=subprocess.CREATE_NEW_CONSOLE)

    def choose_app(self, applications, pos):
        """Show menu to choose from list of applications"""
        import ayon_core.style
        from qtpy import QtWidgets

        menu = QtWidgets.QMenu()
        menu.setStyleSheet(ayon_core.style.load_stylesheet())

        # Sort applications
        applications = sorted(
            applications.items(),
            key=lambda item: item[1].full_label
        )

        for app_name, app in applications:
            icon = get_application_qt_icon(app)

            menu_action = QtWidgets.QAction(app.full_label, parent=menu)
            if icon:
                menu_action.setIcon(icon)
            menu_action.setData((app_name, app))
            menu.addAction(menu_action)

        result = menu.exec_(pos)
        if result:
            return result.data()

    def get_applications(self, project_name):
        """Return the enabled applications for the project"""
        from ayon_core.lib import ApplicationManager

        # Get applications
        manager = ApplicationManager()

        # Create mongo connection
        project_entity = get_project(project_name,
                                     fields=["attrib.applications"])
        assert project_entity, "Project not found. This is a bug."

        # Filter to apps valid for this current project, with logic from:
        # `ayon_core.tools.launcher.models.actions.ApplicationAction.is_compatible`  # noqa
        applications = {}
        for app_name in project_entity["attrib"].get("applications", []):
            app = manager.applications.get(app_name)
            if not app or not app.enabled:
                continue
            applications[app_name] = app

        return applications
