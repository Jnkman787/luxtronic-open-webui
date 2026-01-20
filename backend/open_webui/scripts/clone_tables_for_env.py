#!/usr/bin/env python3
"""
Clone existing production tables with environment-specific suffixes.

This script reads the structure of existing (production) tables and creates
copies with the appropriate environment suffix (e.g., user_dev, chat_dev).

It properly handles:
- Table name suffixes
- Constraint name suffixes
- Foreign key references (updated to point to suffixed tables)

Usage:
    ENV=dev python -m open_webui.scripts.clone_tables_for_env
    ENV=staging python -m open_webui.scripts.clone_tables_for_env
"""

import logging
import re
import sys

from sqlalchemy import inspect, text

from open_webui.env import ENV, OPEN_WEBUI_DIR
from open_webui.internal.db import engine, TABLE_SUFFIX

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Tables that should be cloned for each environment
# Hardcoded list to avoid cloning tables from other apps sharing this database
TABLES_TO_CLONE = [
    # Base tables (no foreign keys to other app tables)
    "auth",
    "channel",
    "channel_member",
    "chat",
    "chatidtag",
    "config",
    "document",
    "email_2fa_challenge",
    "feedback",
    "file",
    "folder",
    "function",
    "group",
    "knowledge",
    "memory",
    "message",
    "message_reaction",
    "model",
    "note",
    "oauth_session",
    "prompt",
    "tag",
    "tenant",
    "tenant_rebuild_schedule",
    "tool",
    "user",
]


def update_foreign_key_references(create_stmt: str, suffix: str, tables_to_clone: list[str]) -> str:
    """
    Update foreign key references in CREATE TABLE statement to point to suffixed tables.

    Example:
        REFERENCES `tenant` (`id`) -> REFERENCES `tenant_dev` (`id`)
    """
    # Pattern to match REFERENCES `table_name` (`column`)
    # We only update references to tables that are in our clone list
    for table in tables_to_clone:
        # Match REFERENCES `table` (with word boundary to avoid partial matches)
        pattern = rf'REFERENCES `{table}`(\s*\()'
        replacement = rf'REFERENCES `{table}{suffix}`\1'
        create_stmt = re.sub(pattern, replacement, create_stmt)

    return create_stmt


def clone_tables():
    """
    Clone production tables with environment suffix.
    """
    from alembic import command
    from alembic.config import Config

    # Safety check
    if ENV in ("prod", "production", ""):
        log.error("This script should not be used for production environments.")
        sys.exit(1)

    if not TABLE_SUFFIX:
        log.error("No table suffix defined for this environment.")
        sys.exit(1)

    log.info(f"Cloning tables for environment: {ENV}")
    log.info(f"Table suffix: {TABLE_SUFFIX}")

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    log.info(f"Tables to clone: {TABLES_TO_CLONE}")

    created_tables = []
    skipped_tables = []
    failed_tables = []

    with engine.connect() as conn:
        # Disable FK checks during table creation to handle circular dependencies
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))

        for base_table in TABLES_TO_CLONE:
            new_table_name = f"{base_table}{TABLE_SUFFIX}"

            # Skip if already exists
            if new_table_name in existing_tables:
                log.info(f"Table '{new_table_name}' already exists, skipping.")
                skipped_tables.append(new_table_name)
                continue

            # Check if source table exists
            if base_table not in existing_tables:
                log.warning(f"Source table '{base_table}' not found, skipping.")
                continue

            # Get the CREATE TABLE statement from the original table
            try:
                result = conn.execute(text(f"SHOW CREATE TABLE `{base_table}`"))
                row = result.fetchone()
                if row:
                    create_stmt = row[1]

                    # 1. Replace the table name
                    new_create_stmt = create_stmt.replace(
                        f"CREATE TABLE `{base_table}`",
                        f"CREATE TABLE `{new_table_name}`",
                        1
                    )

                    # 2. Replace constraint names to avoid conflicts
                    new_create_stmt = re.sub(
                        r'CONSTRAINT `([^`]+)`',
                        lambda m: f'CONSTRAINT `{m.group(1)}{TABLE_SUFFIX}`',
                        new_create_stmt
                    )

                    # 3. Update foreign key references to point to suffixed tables
                    new_create_stmt = update_foreign_key_references(
                        new_create_stmt, TABLE_SUFFIX, TABLES_TO_CLONE
                    )

                    # 4. Also update index names to avoid conflicts
                    new_create_stmt = re.sub(
                        r'KEY `([^`]+)`',
                        lambda m: f'KEY `{m.group(1)}{TABLE_SUFFIX}`' if not m.group(1).startswith('PRIMARY') else m.group(0),
                        new_create_stmt
                    )

                    log.info(f"Creating table '{new_table_name}'...")
                    conn.execute(text(new_create_stmt))
                    created_tables.append(new_table_name)
                    log.info(f"  Created '{new_table_name}' successfully.")

            except Exception as e:
                log.error(f"Failed to create '{new_table_name}': {e}")
                failed_tables.append(new_table_name)
                continue

        # Re-enable FK checks
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        conn.commit()

    log.info("")
    log.info(f"Created {len(created_tables)} tables: {created_tables}")
    if skipped_tables:
        log.info(f"Skipped {len(skipped_tables)} existing tables: {skipped_tables}")
    if failed_tables:
        log.error(f"Failed {len(failed_tables)} tables: {failed_tables}")

    # Create the alembic version table for this environment
    version_table = f"alembic_version{TABLE_SUFFIX}"
    if version_table not in existing_tables:
        log.info(f"Creating Alembic version table '{version_table}'...")
        conn = engine.connect()
        conn.execute(text(f"""
            CREATE TABLE `{version_table}` (
                version_num VARCHAR(32) NOT NULL,
                CONSTRAINT `{version_table}_pkc` PRIMARY KEY (version_num)
            )
        """))
        conn.commit()
        conn.close()

    # Stamp Alembic to head
    log.info("Stamping Alembic to head...")
    alembic_cfg = Config(OPEN_WEBUI_DIR / "alembic.ini")
    alembic_cfg.set_main_option("script_location", str(OPEN_WEBUI_DIR / "migrations"))
    command.stamp(alembic_cfg, "head")

    log.info("")
    log.info(f"Database setup complete for environment: {ENV}")
    log.info(f"You can now start the application with ENV={ENV}")


if __name__ == "__main__":
    clone_tables()
