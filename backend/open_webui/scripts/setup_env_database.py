#!/usr/bin/env python3
"""
Setup script for dev/staging database environments.

This script creates all database tables with environment-specific suffixes
(e.g., user_dev, chat_dev for ENV=dev) and stamps Alembic to the current head.

Usage:
    ENV=dev python -m open_webui.scripts.setup_env_database
    ENV=staging python -m open_webui.scripts.setup_env_database

Note: This should only be used for initial setup of dev/staging environments.
Production should continue to use normal Alembic migrations.
"""

import logging
import sys

from sqlalchemy import inspect, text

from open_webui.env import ENV, OPEN_WEBUI_DIR
from open_webui.internal.db import Base, engine, get_table_name, TABLE_SUFFIX

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def setup_database():
    """
    Set up the database for dev/staging environments.

    1. Creates all tables using SQLAlchemy models (with environment suffixes)
    2. Stamps Alembic to head (so it doesn't try to run old migrations)
    """
    from alembic import command
    from alembic.config import Config

    # Safety check: Don't run this for production
    if ENV in ("prod", "production", ""):
        log.error(
            "This script should not be used for production environments. "
            "Use 'alembic upgrade head' instead."
        )
        sys.exit(1)

    log.info(f"Setting up database for environment: {ENV}")
    log.info(f"Table suffix: {TABLE_SUFFIX or '(none)'}")

    # Check current state
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    version_table = f"alembic_version{TABLE_SUFFIX}"

    log.info(f"Environment-specific Alembic version table: {version_table}")

    # If version table exists, check if we need to reset it
    if version_table in existing_tables:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT version_num FROM `{version_table}`"))
            current_version = result.fetchone()
            if current_version:
                log.warning(
                    f"Alembic version table '{version_table}' already exists at version: {current_version[0]}. "
                    "This script will reset it to head after creating missing tables."
                )
                # Drop the version table to reset state
                conn.execute(text(f"DROP TABLE `{version_table}`"))
                conn.commit()
                log.info(f"Dropped existing '{version_table}' table to reset migration state.")

    # Import all models to ensure they're registered with Base.metadata
    # This is necessary for create_all() to know about all tables
    log.info("Importing models...")
    from open_webui.models import (
        auths,
        channels,
        chats,
        email_2fa,
        feedbacks,
        files,
        folders,
        functions,
        groups,
        knowledge,
        memories,
        messages,
        models,
        notes,
        oauth_sessions,
        prompts,
        tags,
        tenants,
        tools,
        users,
    )
    from open_webui import config  # For the Config table

    log.info("Running migrations to create tables with environment suffix...")

    alembic_cfg = Config(OPEN_WEBUI_DIR / "alembic.ini")
    alembic_cfg.set_main_option("script_location", str(OPEN_WEBUI_DIR / "migrations"))

    # Run all migrations from scratch
    # Migrations have been updated to use get_table_name() for environment-aware table names
    try:
        command.upgrade(alembic_cfg, "head")
        log.info("Migrations completed successfully.")
    except Exception as e:
        log.error(f"Migration failed: {e}")
        log.error("Some tables may need to be created manually or migrations may need updating.")
        raise

    # List created/existing tables
    inspector = inspect(engine)
    new_tables = set(inspector.get_table_names())
    env_tables = [t for t in new_tables if t.endswith(TABLE_SUFFIX)]
    log.info(f"Environment-specific tables ({len(env_tables)}): {sorted(env_tables)}")

    # Stamp Alembic to head
    log.info("Stamping Alembic to head...")

    alembic_cfg = Config(OPEN_WEBUI_DIR / "alembic.ini")
    alembic_cfg.set_main_option("script_location", str(OPEN_WEBUI_DIR / "migrations"))

    # Stamp to head - this marks all existing migrations as "applied"
    # without actually running them
    command.stamp(alembic_cfg, "head")

    log.info("Alembic stamped to head.")
    log.info(f"Database setup complete for environment: {ENV}")
    log.info("")
    log.info("You can now start the application with ENV={ENV}")


if __name__ == "__main__":
    setup_database()
