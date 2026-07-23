#!/bin/sh
set -eu

REPO_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

docker compose -f "$REPO_DIR/docker/compose.dev.yml" exec -T mysql sh -lc \
  'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "
    CREATE DATABASE IF NOT EXISTS devflow_migration_test
      CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
    GRANT ALL PRIVILEGES ON devflow_migration_test.* TO '\''devflow'\''@'\''%'\'';
    FLUSH PRIVILEGES;
  "'

cd "$REPO_DIR/backend"
MYSQL_DATABASE=devflow_migration_test .venv/bin/alembic upgrade head

echo "测试数据库 devflow_migration_test 已准备完成"
