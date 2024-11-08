import subprocess
import contextlib
import tempfile
import os
import asyncio
from typing import Optional, Iterable, Callable

import clique

from ayon_core.lib import get_oiio_tool_args

VERBOSE = False


async def run_subprocess_async(cmd: "list[str] | str") -> "tuple[str, str]":
    """Run subprocess asynchronously and return stdout and stderr."""
    if isinstance(cmd, str):
        cmd = [cmd]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return stdout.decode(), stderr.decode()


async def update_qt(app):
    """Update Qt event loop indefinitely until task ends."""
    if not app:
        return
    while True:
        app.processEvents()
        await asyncio.sleep(0.01)


async def create_tasks_pool(tasks, max_concurrent=100):
    """Run async tasks in a pool with a maximum number of concurrent tasks."""

    # Task runner within semaphore
    async def _task_runner(semaphore, task):
        async with semaphore:
            return await task

    semaphore = asyncio.Semaphore(max_concurrent)

    result = await asyncio.gather(
        *(_task_runner(semaphore, task) for task in tasks)
    )

    return result


async def process_files_in_pool(
    filepaths: Iterable[str],
    processor: Callable,
    pool_size=15
):
    """Process files in parallel using a pool of subprocesses."""
    # TODO: We may want to raise an error or stop the pool if one of the
    #  processes returned an error code that was not 0
    tasks = [processor(file) for file in filepaths]
    return await create_tasks_pool(tasks, max_concurrent=pool_size)


@contextlib.contextmanager
def background_task(task):
    """Run background task and cancel it when context exits.

    Examples:
        >>> with background_task(update_qt(app)):
        >>>     # Do something else
        >>>     pass

    Args:
        task (Coroutine): Task to run in the background.
    """
    if not task:
        return

    background = asyncio.create_task(task)
    try:
        yield
    finally:
        background.cancel()



async def generate_apng(
        input_sequence: clique.Collection,
        apngc_executable: str,
        apngc_settings_profile: str,
        tinify_api_key: Optional[str] = None
) -> str:
    """Generate APNG file from input sequence using APNGC CLI.

    The APNGC CLI uses Tinify to compress the resulting APNG file, so either
    the settings profile itself must specify a valid Tinify API key, or the
    `tinify_api_key` argument must be provided.

    Args:
        input_sequence: Input sequence to convert to APNG.
        apngc_executable: Path to the APNGC executable.
        apngc_settings_profile: Path to the APNGC settings .json profile.
            This must be an existing .json file on disk.
        tinify_api_key: Optional Tinify API key to use for compression.

    Returns:
        str: Path to the generated APNG file.
    """
    # Enforce padding on sequence if not set to be length of first frame
    # This fixes some cases if `clique.assemble` was not called with
    # `assume_padded_when_ambiguous=True`
    if not input_sequence.padding:
        input_sequence.padding = len(str(list(input_sequence.indexes)[0]))

    with contextlib.ExitStack() as stack:
        # Generate PNG sequence
        png_folder = stack.enter_context(
            tempfile.TemporaryDirectory(prefix="transcoding_", suffix="_png"))

        async def convert_to_png(
                input_path
        ):
            fname = os.path.splitext(os.path.basename(input_path))[0] + ".png"
            output_path = os.path.join(png_folder, fname)
            # Convert using `iconvert` because it actually converts the alpha
            # correctly instead of darkening the image like `ffmpeg` seems to do
            iconvert = get_oiio_tool_args(
                "iconvert",
                "-d", "uint8",
                "--sRGB",
                "--clear-keywords",
                input_path,
                output_path
            )
            result = await run_subprocess_async(iconvert)
            print("Converted", input_path, "to PNG:", output_path)
            if VERBOSE:
                print(result)

            return result

        # TODO: Skip conversion if input is already png?
        await process_files_in_pool(input_sequence, convert_to_png)
        print(f"Converted {input_sequence} to PNG to: {png_folder}")

        # Generate APNG using `apngc` CLI
        # Note: APNGC processes a folder of PNGs - and will include *all*
        # files. So we should isolate the PNG files we want into a dedicated
        # temp folder
        apng_folder = tempfile.TemporaryDirectory(prefix="transcoding_",
                                                  suffix="_apng").name
        apngc_args = [
            apngc_executable,
            "headless",
            "--settings",
            apngc_settings_profile,
            "--folder",
            png_folder,
            "--output_path",
            apng_folder,
        ]
        if tinify_api_key:
            apngc_args.extend([
                "--tinify",
                tinify_api_key
            ])

        print(f"Running {subprocess.list2cmdline(apngc_args)}")
        await run_subprocess_async(apngc_args)

        # There should just be a single PNG file in this temp folder
        filename = os.listdir(apng_folder)[0]
        filepath = os.path.join(apng_folder, filename)
        print(f"Finished APNG generation: {filepath}")
        return filepath
