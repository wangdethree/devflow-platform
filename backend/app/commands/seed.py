"""幂等初始化 DevFlow 基础数据。

用法：
    python -m app.commands.seed
    python -m app.commands.seed --admin-email admin@example.com \
        --admin-username admin --admin-password '安全密码'
"""

import argparse
import asyncio

from app.database.session import AsyncSessionLocal, engine
from app.services.seed_service import seed_admin, seed_reference_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="初始化 DevFlow 基础数据")
    parser.add_argument("--admin-email")
    parser.add_argument("--admin-username", default="admin")
    parser.add_argument("--admin-password")
    return parser.parse_args()


async def run() -> None:
    """执行幂等初始化并释放数据库引擎。"""

    args = parse_args()
    if bool(args.admin_email) != bool(args.admin_password):
        raise SystemExit("admin-email 与 admin-password 必须同时提供")

    async with AsyncSessionLocal() as session:
        await seed_reference_data(session)
        if args.admin_email:
            await seed_admin(
                session,
                email=args.admin_email,
                username=args.admin_username,
                password=args.admin_password,
            )
    await engine.dispose()
    print("DevFlow 基础数据初始化完成")


if __name__ == "__main__":
    asyncio.run(run())
