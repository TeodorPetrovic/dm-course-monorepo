#!/usr/bin/env bash
# (Re)kreira lokalnu bazu dm_local: šema + seed iz Day 1 CSV-ova. Briše SAMO lokalnu dm_local bazu.
set -euo pipefail
D="$(cd "$(dirname "$0")" && pwd)"
"$D/start_local_db.sh" >/dev/null
"$D/../apps/api/.venv/bin/python" "$D/seed.py" "$@"
M="mariadb --no-defaults --socket=$D/mysqld.sock -udm_local -pdm_local dm_local"
$M < "$D/schema.sql"; $M < "$D/seed.sql"
$M -N -e "SELECT CONCAT('category=',(SELECT COUNT(*) FROM category),' product=',(SELECT COUNT(*) FROM product),' seo=',(SELECT COUNT(*) FROM seo),' event=',(SELECT COUNT(*) FROM event))"
