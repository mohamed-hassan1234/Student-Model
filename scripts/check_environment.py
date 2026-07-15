import argparse
import asyncio
import shutil
from collections.abc import Sequence

from devmind_api.config import Settings
from devmind_api.db import MongoManager

REQUIRED_TOOLS = ("uv", "node", "npm")


def check_required_tools() -> list[str]:
    missing: list[str] = []
    for tool in REQUIRED_TOOLS:
        if shutil.which(tool) is None:
            missing.append(tool)
    return missing


async def check_mongodb(settings: Settings) -> bool:
    manager = MongoManager(settings)
    try:
        await manager.connect()
        return await manager.ping()
    finally:
        await manager.close()


async def run(mongodb_only: bool) -> int:
    settings = Settings()
    if not mongodb_only:
        missing = check_required_tools()
        if missing:
            print(f"Missing required tools: {', '.join(missing)}")
            return 1
        print("Required tools found.")

    try:
        mongodb_ok = await check_mongodb(settings)
    except Exception as exc:
        print(f"MongoDB connectivity check failed: {exc.__class__.__name__}")
        return 1

    if mongodb_ok:
        print("MongoDB connectivity check passed.")
        return 0
    print("MongoDB ping returned an unexpected result.")
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check DevMind AI local environment.")
    parser.add_argument(
        "--mongodb-only", action="store_true", help="Only verify MongoDB connectivity."
    )
    args = parser.parse_args(argv)
    return asyncio.run(run(mongodb_only=args.mongodb_only))


if __name__ == "__main__":
    raise SystemExit(main())
