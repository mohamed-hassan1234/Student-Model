import argparse
import asyncio

from devmind_api.auth.repositories import AuthRepository
from devmind_api.auth.services import AuthService, AuthServiceError
from devmind_api.config import get_settings
from devmind_api.db import MongoManager


async def _bootstrap_admin(args: argparse.Namespace) -> None:
    settings = get_settings()
    manager = MongoManager(settings)
    await manager.connect()
    try:
        if manager.database is None:
            raise RuntimeError("MongoDB database is not available")
        service = AuthService(AuthRepository(manager.database), settings)
        user = await service.bootstrap_admin(args.email, args.username, args.password)
        print(f"Created super administrator: {user.email}")
    finally:
        await manager.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DevMind AI authentication administration")
    subcommands = parser.add_subparsers(dest="command", required=True)
    bootstrap = subcommands.add_parser("bootstrap-admin", help="Create the first super admin")
    bootstrap.add_argument("--email", required=True)
    bootstrap.add_argument("--username", required=True)
    bootstrap.add_argument("--password", required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "bootstrap-admin":
        try:
            asyncio.run(_bootstrap_admin(args))
        except (AuthServiceError, ValueError, RuntimeError) as exc:
            raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
