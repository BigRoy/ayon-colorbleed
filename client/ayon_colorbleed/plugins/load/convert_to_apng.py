import os
import shutil
import time
import asyncio

from qtpy import QtWidgets
import clique

from ayon_core.lib import is_running_from_build, EnumDef
from ayon_core.pipeline import load
from ayon_core.pipeline.context_tools import get_project_settings

from ayon_colorbleed import lib

# TODO: Remove forced reload if not in dev mode
import importlib
importlib.reload(lib)

def run_task_with_qt_update(task):
    async def runner(_task):
        app = QtWidgets.QApplication.instance()
        with lib.background_task(lib.update_qt(app)):
            return await _task
    return asyncio.run(runner(task))


class ConvertToAPNG(load.LoaderPlugin):
    """Convert image sequence to APNG using APNGC CLI."""

    tool_names = ["library_loader"]
    product_types = {"*"}
    representations = {"*"}
    extensions = {"png", "jpg", "jpeg", "tiff", "tif", "exr"}

    enabled = (
        not is_running_from_build() or
        os.getenv("AYON_USE_DEV") == "1"
    )

    label = "Convert to APNG"
    order = 9999
    icon = "compress"
    color = "#7289da"

    _apngc_settings = {}

    @classmethod
    def get_apngc_settings(cls, project_name):
        # Cache for as long as loader is in memory
        if cls._apngc_settings.get(project_name) is None:
            settings = get_project_settings(project_name)
            apngc_settings = settings.get("colorbleed", {}).get("apngc", {})
            cls._apngc_settings[project_name] = apngc_settings
        return cls._apngc_settings[project_name]

    @classmethod
    def get_options(cls, contexts):
        context = contexts[0]
        project_name = context["project"]["name"]
        settings_profile = cls.get_apngc_settings(project_name)
        profiles: list[str] = settings_profile.get("profiles")
        if not profiles:
            return []

        return [
            EnumDef(
                "profile", items=[{
                    "value": profile,
                    "label": os.path.basename(profile)
                } for profile in profiles]
            )
        ]
    @classmethod
    def is_compatible_loader(cls, context):
        if context["representation"]["name"] == "thumbnail":
            return False
        return super().is_compatible_loader(context)

    def load(self, context, name=None, namespace=None, options=None):
        # TODO: Open popup dialog that logs the output of the conversion
        #       and if possible allow the user to cancel the conversion
        #       or see when it finished.
        # TODO: Run multiples in one batch and at the end of the first open
        #       temporary directory (or at end the end of all) so the user
        #       has access to the files and can do with it whatever they want
        # TODO: Run completely in spawned off process to make it easier to
        #       spawn many. OR submit it to farm on Deadline is probably
        #       better.

        path = self.filepath_from_context(context)
        project_name: str = context["project"]["name"]
        settings_profile = self.get_apngc_settings(project_name)

        profile = options.get("profile")
        if not profile:
            # TODO: Support picking profile dynamically based on context
            raise RuntimeError("Please use with option box.")

        executable = settings_profile.get("executable")
        tinify_api_key = settings_profile.get("tinify_api_key")
        output_directory = settings_profile.get("output_directory")
        if not executable:
            raise ValueError("No APNGC executable path found in settings.")
        if not profile:
            raise ValueError("No APNGC profiles found in settings.")
        if not tinify_api_key:
            raise ValueError("No Tinify API key found in settings.")
        if not output_directory:
            raise ValueError(
                "No conversion output directory found in settings.")

        # Get the sequence
        folder = os.path.dirname(path)
        fname = os.path.basename(path)
        head = fname.split(".")[0]  # head before frame number
        ext = os.path.splitext(fname)[-1]
        sequence = [
            os.path.join(folder, fname) for fname in os.listdir(folder)
            if fname.startswith(head) and fname.endswith(ext)
        ]

        collections, remainder = clique.assemble(
            sequence,
            assume_padded_when_ambiguous=True)
        assert not remainder, f"No sequence collection found for {path}"
        collection = collections[0]

        # Ensure output folder can exist
        os.makedirs(output_directory, exist_ok=True)

        print(f"Converting {collection}")
        task = lib.generate_apng(
            collection,
            apngc_executable=executable,
            apngc_settings_profile=profile,
            tinify_api_key=tinify_api_key
        )
        filepath = run_task_with_qt_update(task)

        # Copy the file to the output location
        fname = os.path.basename(filepath)
        head, ext = os.path.splitext(fname)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        fname = f"{head}_{timestamp}{ext}"
        output_filepath = os.path.join(output_directory, fname)
        shutil.copyfile(filepath, output_filepath)
        print(f"Copied output file: {output_filepath}")