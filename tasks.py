"""Tasks for use with Invoke."""

import os

from invoke import task

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def is_truthy(arg):
    """Convert "truthy" strings into Booleans.

    Examples:
        >>> is_truthy('yes')
        True

    Args:
        arg (str): Truthy string (True values are y, yes, t, true, on and 1; false values are n, no,
        f, false, off and 0. Raises ValueError if val is anything else.
    """
    if isinstance(arg, bool):
        return arg
    val = str(arg).lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    if val in ("n", "no", "f", "false", "off", "0"):
        return False
    raise ValueError(f"Invalid truthy value: `{arg}`")


with open("pyproject.toml", "rb") as _f:
    PYPROJECT_CONFIG = tomllib.load(_f)
TOOL_CONFIG = PYPROJECT_CONFIG["tool"]["poetry"]

# Can be set to a separate Python version to be used for launching or building image
PYTHON_VER = os.getenv("PYTHON_VER", "3.12")
# Name of the docker image/image
IMAGE_NAME = os.getenv("IMAGE_NAME", TOOL_CONFIG["name"])
# Tag for the image
IMAGE_VER = os.getenv("IMAGE_VER", f"{TOOL_CONFIG['version']}-py{PYTHON_VER}")
# Gather current working directory for Docker commands
PWD = os.getcwd()
# Local or Docker execution provide "local" to run locally without docker execution
INVOKE_LOCAL = is_truthy(os.getenv("INVOKE_LOCAL", False))


def run_cmd(context, exec_cmd, local=INVOKE_LOCAL):
    """Wrapper to run the invoke task commands.

    Args:
        context ([invoke.task]): Invoke task object.
        exec_cmd ([str]): Command to run.
        local (bool): Define as `True` to execute locally

    Returns:
        result (obj): Contains Invoke result from running task.
    """
    if is_truthy(local):
        print(f"LOCAL - Running command {exec_cmd}")
        result = context.run(exec_cmd, pty=True)
    else:
        print(f"DOCKER - Running command: {exec_cmd} container: {IMAGE_NAME}:{IMAGE_VER}")
        result = context.run(f"docker run -it -v {PWD}:/local {IMAGE_NAME}:{IMAGE_VER} sh -c '{exec_cmd}'", pty=True)

    return result


@task(
    help={
        "cache": "Whether to use Docker's cache when building images (default enabled)",
        "force_rm": "Always remove intermediate images",
        "hide": "Suppress output from Docker",
    }
)
def build(context, cache=True, force_rm=False, hide=False):
    """Build a Docker image."""
    print(f"Building image {IMAGE_NAME}:{IMAGE_VER}")
    command = f"docker build --tag {IMAGE_NAME}:{IMAGE_VER} --build-arg PYTHON_VER={PYTHON_VER} -f Dockerfile ."

    if not cache:
        command += " --no-cache"
    if force_rm:
        command += " --force-rm"

    result = context.run(command, hide=hide)
    if result.exited != 0:
        print(f"Failed to build image {IMAGE_NAME}:{IMAGE_VER}\nError: {result.stderr}")


@task
def clean(context):
    """Remove the project specific image."""
    print(f"Attempting to forcefully remove image {IMAGE_NAME}:{IMAGE_VER}")
    context.run(f"docker rmi {IMAGE_NAME}:{IMAGE_VER} --force")
    print(f"Successfully removed image {IMAGE_NAME}:{IMAGE_VER}")


@task
def rebuild(context):
    """Clean the Docker image and then rebuild without using cache."""
    clean(context)
    build(context, cache=False)


@task(help={"local": "Run locally or within the Docker container"})
def pytest(context, local=INVOKE_LOCAL):
    """Run pytest test cases."""
    exec_cmd = "pytest"
    run_cmd(context, exec_cmd, local)


@task(
    help={
        "action": "One of 'lint' or 'format'",
        "fix": "Automatically fix issues",
        "local": "Run locally or within the Docker container",
    }
)
def ruff(context, action=None, fix=False, local=INVOKE_LOCAL):
    """Run ruff for code formatting and linting."""
    if action is None:
        actions = ["format", "lint"]
    else:
        actions = [action]

    for act in actions:
        if act == "format":
            command = "ruff format"
            if not fix:
                command += " --check"
            command += " ."
        elif act == "lint":
            command = "ruff check"
            if fix:
                command += " --fix"
            command += " ."
        else:
            raise ValueError(f"Invalid ruff action: {act}. Must be 'lint' or 'format'.")
        run_cmd(context, command, local)


@task(help={"local": "Run locally or within the Docker container"})
def yamllint(context, local=INVOKE_LOCAL):
    """Run yamllint to validate YAML formatting."""
    exec_cmd = "yamllint ."
    run_cmd(context, exec_cmd, local)


@task
def cli(context):
    """Enter the image to perform troubleshooting or dev work."""
    dev = f"docker run -it -v {PWD}:/local {IMAGE_NAME}:{IMAGE_VER} /bin/bash"
    context.run(f"{dev}", pty=True)


@task(help={"local": "Run locally or within the Docker container"})
def tests(context, local=INVOKE_LOCAL):
    """Run all tests for this repository."""
    ruff(context, local=local)
    yamllint(context, local=local)
    pytest(context, local=local)

    print("All tests have passed!")
