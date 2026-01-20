#!/usr/bin/env python3
"""
Drop all environment-specific tables (_dev, _staging).

Usage:
    python -m open_webui.scripts.drop_env_tables --suffix _dev
    python -m open_webui.scripts.drop_env_tables --suffix _staging
    python -m open_webui.scripts.drop_env_tables --suffix _dev --suffix _staging
"""

import argparse
import logging
import sys

from sqlalchemy import inspect, text

from open_webui.internal.db import engine

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def drop_env_tables(suffixes: list[str], dry_run: bool = False):
    """Drop all tables with the specified suffixes."""

    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    tables_to_drop = []
    for table in existing_tables:
        for suffix in suffixes:
            if table.endswith(suffix):
                tables_to_drop.append(table)
                break

    if not tables_to_drop:
        log.info(f"No tables found with suffixes: {suffixes}")
        return

    log.info(f"Found {len(tables_to_drop)} tables to drop: {sorted(tables_to_drop)}")

    if dry_run:
        log.info("Dry run - no tables dropped")
        return

    with engine.connect() as conn:
        # Disable FK checks temporarily
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))

        for table in tables_to_drop:
            log.info(f"Dropping table: {table}")
            conn.execute(text(f"DROP TABLE IF EXISTS `{table}`"))

        # Re-enable FK checks
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        conn.commit()

    log.info(f"Dropped {len(tables_to_drop)} tables")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Drop environment-specific tables")
    parser.add_argument("--suffix", action="append", required=True,
                        help="Table suffix to drop (e.g., _dev, _staging)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be dropped without actually dropping")

    args = parser.parse_args()
    drop_env_tables(args.suffix, args.dry_run)
