import sys
from logging import error
from tomllib import load


async def shutdown():
    error("Bot shutdowned by command")
    sys.exit(0)


async def get_version_from_pyproject() -> str:
    with open("pyproject.toml", "rb") as f:
        data = load(f)
    return data["project"]["version"]
