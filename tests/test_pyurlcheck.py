"""Testing for pyurlcheck."""

import pathlib

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from pyurlcheck import __version__


def test_version():
    """Simple version test."""
    pyproject_path = pathlib.Path(__file__).resolve().parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)
    poetry_version = pyproject["tool"]["poetry"]["version"]
    assert __version__ == poetry_version
