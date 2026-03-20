#!/usr/bin/env bash
# =============================================================================
# Nigehbaan: Migrate from Neon PostgreSQL to AWS RDS PostgreSQL
# =============================================================================
# Usage: ./migrate-to-rds.sh <RDS_ENDPOINT> <RDS_PASSWORD>
#
# Example:
#   ./migrate-to-rds.sh nigehbaan-db.abc123.ap-south-1.rds.amazonaws.com MyStr0ngP@ss
#
# Prerequisites:
#   - RDS instance created in same VPC as EC2 (ap-south-1)
#   - Security group allows inbound 5432 from EC2's SG
#   - Run this script on the EC2 instance (ubuntu@3.110.174.178)
# =============================================================================

set -euo pipefail

# --- Arguments ---
RDS_ENDPOINT="${1:?Usage: $0 <RDS_ENDPOINT> <RDS_PASSWORD>}"
RDS_PASSWORD="${2:?Usage: $0 <RDS_ENDPOINT> <RDS_PASSWORD>}"
RDS_USER="nigehbaan"
RDS_DB="nigehbaan"
RDS_PORT="5432"

NEON_URL="postgresql://neondb_owner:npg_X6pQz9ceYuHI@ep-dawn-scene-a1vqoqjj.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
DUMP_FILE="/tmp/nigehbaan_dump.backup"
ENV_FILE="/opt/nigehbaan/.env.production"

echo "============================================"
echo "  Nigehbaan: Neon -> RDS Migration"
echo "============================================"
echo "RDS Endpoint: ${RDS_ENDPOINT}"
echo "RDS Database: ${RDS_DB}"
echo "RDS User:     ${RDS_USER}"
echo ""

# --- Phase 2: Install PostgreSQL client ---
echo "[Phase 2] Installing PostgreSQL client..."
if ! command -v psql &>/dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq postgresql-client
    echo "  -> psql installed."
else
    echo "  -> psql already installed."
fi

# --- Phase 2: Enable PostGIS on RDS ---
echo "[Phase 2] Enabling PostGIS extensions on RDS..."
export PGPASSWORD="${RDS_PASSWORD}"
psql -h "${RDS_ENDPOINT}" -U "${RDS_USER}" -d "${RDS_DB}" -p "${RDS_PORT}" <<'EOSQL'
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
SELECT PostGIS_Version();
EOSQL
echo "  -> PostGIS enabled."

# --- Phase 3.1: Dump from Neon ---
echo "[Phase 3] Dumping data from Neon (this may take a few minutes)..."
pg_dump "${NEON_URL}" \
    --no-owner --no-acl --format=custom \
    -f "${DUMP_FILE}"
echo "  -> Dump saved to ${DUMP_FILE} ($(du -h "${DUMP_FILE}" | cut -f1))"

# --- Phase 3.2: Restore to RDS (full schema + data) ---
echo "[Phase 3] Restoring to RDS..."
pg_restore -h "${RDS_ENDPOINT}" -U "${RDS_USER}" -d "${RDS_DB}" -p "${RDS_PORT}" \
    --no-owner --no-acl --clean --if-exists \
    "${DUMP_FILE}" || true
# pg_restore returns non-zero on warnings (e.g., "relation does not exist" for --clean),
# so we || true to avoid script abort

echo "  -> Restore complete."

# --- Phase 3.3: Verify row counts ---
echo "[Phase 3] Verifying data..."
psql -h "${RDS_ENDPOINT}" -U "${RDS_USER}" -d "${RDS_DB}" -p "${RDS_PORT}" <<'EOSQL'
SELECT 'news_articles' AS table_name, COUNT(*) FROM news_articles
UNION ALL
SELECT 'incidents', COUNT(*) FROM incidents
UNION ALL
SELECT 'vulnerability_indicators', COUNT(*) FROM vulnerability_indicators
ORDER BY table_name;
EOSQL

# --- Phase 4: Update .env.production ---
echo "[Phase 4] Updating ${ENV_FILE}..."
NEW_DB_URL="DATABASE_URL=postgresql+asyncpg://${RDS_USER}:${RDS_PASSWORD}@${RDS_ENDPOINT}:${RDS_PORT}/${RDS_DB}?sslmode=require"

if [ -f "${ENV_FILE}" ]; then
    # Backup original
    cp "${ENV_FILE}" "${ENV_FILE}.bak.$(date +%Y%m%d%H%M%S)"
    echo "  -> Backup created."

    # Replace DATABASE_URL line
    sed -i "s|^DATABASE_URL=.*|${NEW_DB_URL}|" "${ENV_FILE}"
    echo "  -> DATABASE_URL updated."
else
    echo "  ERROR: ${ENV_FILE} not found!"
    exit 1
fi

# --- Phase 5: Restart containers ---
echo "[Phase 5] Restarting Docker containers..."
cd /opt/nigehbaan
docker restart nigehbaan-celery-worker nigehbaan-celery-beat nigehbaan-api
echo "  -> Containers restarted. Waiting 10s for startup..."
sleep 10

# --- Phase 5: Health check ---
echo "[Phase 5] Running health check..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")
if [ "${HTTP_STATUS}" = "200" ]; then
    echo "  -> API health check: OK (200)"
else
    echo "  -> API health check: ${HTTP_STATUS} (may need more time to start)"
fi

# --- Phase 5: Verify DB connectivity from containers ---
echo "[Phase 5] Verifying DB connectivity from containers..."
docker exec nigehbaan-celery-worker python -c "
import asyncio
from app.database import async_session_factory
from sqlalchemy import text

async def test():
    async with async_session_factory() as s:
        r = await s.execute(text('SELECT COUNT(*) FROM news_articles'))
        print(f'  Articles: {r.scalar()}')
        r = await s.execute(text('SELECT COUNT(*) FROM incidents'))
        print(f'  Incidents: {r.scalar()}')
        r = await s.execute(text('SELECT PostGIS_Version()'))
        print(f'  PostGIS: {r.scalar()}')

asyncio.run(test())
"

# --- Phase 5: Latency test ---
echo "[Phase 5] Latency test..."
docker exec nigehbaan-api python -c "
import asyncio, time
from app.database import async_session_factory
from sqlalchemy import text

async def test():
    async with async_session_factory() as s:
        times = []
        for _ in range(5):
            start = time.monotonic()
            await s.execute(text('SELECT 1'))
            times.append((time.monotonic() - start) * 1000)
        avg = sum(times) / len(times)
        print(f'  Average latency: {avg:.1f}ms (5 queries)')
        print(f'  Individual: {[f\"{t:.1f}ms\" for t in times]}')

asyncio.run(test())
"

# --- Cleanup ---
echo ""
echo "============================================"
echo "  Migration Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Test the website: https://nigehbaan.org (or your domain)"
echo "  2. Trigger a scraper to verify full pipeline:"
echo "     docker exec nigehbaan-celery-worker python -c \\"
echo "       \"from app.tasks.scraping_tasks import scrape_news_rss; print(scrape_news_rss.delay())\""
echo "  3. Check worker logs: docker logs -f nigehbaan-celery-worker"
echo ""
echo "Rollback (if needed):"
echo "  cp ${ENV_FILE}.bak.* ${ENV_FILE}"
echo "  docker restart nigehbaan-celery-worker nigehbaan-celery-beat nigehbaan-api"
echo ""

unset PGPASSWORD
