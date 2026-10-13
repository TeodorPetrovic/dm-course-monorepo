#!/usr/bin/env bash
# Lokalni MariaDB (MySQL-kompatibilan) samo za lokalni razvoj: sopstveni datadir/socket, port 3307, bez veze sa pravom bazom.
# Korisnik/lozinka su lokalni demo kredencijali (nisu iz .env).
set -euo pipefail
D="$(cd "$(dirname "$0")" && pwd)"; DATA="$D/data"; SOCK="$D/mysqld.sock"; PORT="${DM_DB_PORT:-3307}"
if [ ! -d "$DATA/mysql" ]; then
  mariadb-install-db --no-defaults --datadir="$DATA" --auth-root-authentication-method=normal --skip-test-db > "$D/install.log" 2>&1
fi
if ! mariadb-admin --no-defaults --socket="$SOCK" -uroot ping >/dev/null 2>&1; then
  nohup /usr/sbin/mariadbd --no-defaults --datadir="$DATA" --socket="$SOCK" --port="$PORT" --bind-address=127.0.0.1 \
    --pid-file="$D/mysqld.pid" --log-error="$D/mysqld.err" > /dev/null 2>&1 &
  for i in $(seq 1 30); do mariadb-admin --no-defaults --socket="$SOCK" -uroot ping >/dev/null 2>&1 && break; sleep 1; done
fi
mariadb --no-defaults --socket="$SOCK" -uroot -e "CREATE DATABASE IF NOT EXISTS dm_local CHARACTER SET utf8mb4;
CREATE USER IF NOT EXISTS 'dm_local'@'127.0.0.1' IDENTIFIED BY 'dm_local';
CREATE USER IF NOT EXISTS 'dm_local'@'localhost' IDENTIFIED BY 'dm_local';
GRANT ALL ON dm_local.* TO 'dm_local'@'127.0.0.1'; GRANT ALL ON dm_local.* TO 'dm_local'@'localhost'; FLUSH PRIVILEGES;"
echo "MariaDB radi: 127.0.0.1:$PORT  db=dm_local user=dm_local (socket $SOCK)"
