#!/usr/bin/env python3
"""
Database Backup Utility for Gen-Friend

Usage:
    python scripts/backup.py backup              # Create backup
    python scripts/backup.py restore <file>      # Restore from backup
    python scripts/backup.py list                # List available backups
    python scripts/backup.py cleanup             # Remove old backups
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings


def parse_database_url(url: str) -> dict:
    """Parse database URL into components."""
    # Handle async URLs
    url = url.replace("+asyncpg", "").replace("+aiosqlite", "")
    parsed = urlparse(url)
    return {
        "scheme": parsed.scheme,
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "user": parsed.username,
        "password": parsed.password,
        "database": parsed.path.lstrip("/"),
    }


def get_backup_dir() -> Path:
    """Get backup directory, create if needed."""
    backup_dir = Path(settings.backup_path)
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def backup_postgres(db_info: dict) -> str:
    """Backup PostgreSQL database."""
    backup_dir = get_backup_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"genfriend_backup_{timestamp}.sql"
    filepath = backup_dir / filename

    env = os.environ.copy()
    if db_info["password"]:
        env["PGPASSWORD"] = db_info["password"]

    cmd = [
        "pg_dump",
        "-h", db_info["host"],
        "-p", str(db_info["port"]),
        "-U", db_info["user"],
        "-d", db_info["database"],
        "-F", "c",  # Custom format (compressed)
        "-f", str(filepath),
    ]

    try:
        subprocess.run(cmd, env=env, check=True, capture_output=True)
        print(f"Backup created: {filepath}")
        print(f"Size: {filepath.stat().st_size / 1024 / 1024:.2f} MB")
        return str(filepath)
    except subprocess.CalledProcessError as e:
        print(f"Backup failed: {e.stderr.decode()}")
        sys.exit(1)


def backup_sqlite(db_path: str) -> str:
    """Backup SQLite database."""
    import shutil

    backup_dir = get_backup_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"genfriend_backup_{timestamp}.db"
    filepath = backup_dir / filename

    # SQLite backup is just a file copy
    source = Path(db_path)
    if not source.exists():
        print(f"Database file not found: {source}")
        sys.exit(1)

    shutil.copy2(source, filepath)
    print(f"Backup created: {filepath}")
    print(f"Size: {filepath.stat().st_size / 1024 / 1024:.2f} MB")
    return str(filepath)


def restore_postgres(db_info: dict, backup_file: str):
    """Restore PostgreSQL database from backup."""
    if not Path(backup_file).exists():
        print(f"Backup file not found: {backup_file}")
        sys.exit(1)

    env = os.environ.copy()
    if db_info["password"]:
        env["PGPASSWORD"] = db_info["password"]

    # Confirm before restore
    print(f"WARNING: This will REPLACE all data in database '{db_info['database']}'")
    confirm = input("Type 'RESTORE' to confirm: ")
    if confirm != "RESTORE":
        print("Cancelled.")
        sys.exit(0)

    cmd = [
        "pg_restore",
        "-h", db_info["host"],
        "-p", str(db_info["port"]),
        "-U", db_info["user"],
        "-d", db_info["database"],
        "-c",  # Clean (drop) objects before recreating
        backup_file,
    ]

    try:
        subprocess.run(cmd, env=env, check=True, capture_output=True)
        print(f"Database restored from: {backup_file}")
    except subprocess.CalledProcessError as e:
        print(f"Restore failed: {e.stderr.decode()}")
        sys.exit(1)


def restore_sqlite(db_path: str, backup_file: str):
    """Restore SQLite database from backup."""
    import shutil

    if not Path(backup_file).exists():
        print(f"Backup file not found: {backup_file}")
        sys.exit(1)

    print(f"WARNING: This will REPLACE all data in database")
    confirm = input("Type 'RESTORE' to confirm: ")
    if confirm != "RESTORE":
        print("Cancelled.")
        sys.exit(0)

    shutil.copy2(backup_file, db_path)
    print(f"Database restored from: {backup_file}")


def list_backups():
    """List available backup files."""
    backup_dir = get_backup_dir()
    backups = sorted(backup_dir.glob("genfriend_backup_*"), reverse=True)

    if not backups:
        print("No backups found.")
        return

    print(f"\nAvailable backups in {backup_dir}:\n")
    print(f"{'Filename':<45} {'Size':<12} {'Created'}")
    print("-" * 70)

    for backup in backups:
        stat = backup.stat()
        size = f"{stat.st_size / 1024 / 1024:.2f} MB"
        created = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"{backup.name:<45} {size:<12} {created}")


def cleanup_old_backups():
    """Remove backups older than retention period."""
    backup_dir = get_backup_dir()
    cutoff = datetime.now() - timedelta(days=settings.backup_retention_days)
    backups = backup_dir.glob("genfriend_backup_*")

    removed = 0
    for backup in backups:
        if datetime.fromtimestamp(backup.stat().st_mtime) < cutoff:
            backup.unlink()
            removed += 1
            print(f"Removed: {backup.name}")

    print(f"\nRemoved {removed} old backups (older than {settings.backup_retention_days} days)")


def create_backup():
    """Create database backup based on current configuration."""
    db_info = parse_database_url(settings.database_url)

    if db_info["scheme"] == "postgresql":
        return backup_postgres(db_info)
    elif db_info["scheme"] == "sqlite":
        return backup_sqlite(db_info["database"])
    else:
        print(f"Unsupported database type: {db_info['scheme']}")
        sys.exit(1)


def restore_backup(backup_file: str):
    """Restore database from backup file."""
    db_info = parse_database_url(settings.database_url)

    if db_info["scheme"] == "postgresql":
        restore_postgres(db_info, backup_file)
    elif db_info["scheme"] == "sqlite":
        restore_sqlite(db_info["database"], backup_file)
    else:
        print(f"Unsupported database type: {db_info['scheme']}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Gen-Friend Database Backup Utility")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Backup command
    subparsers.add_parser("backup", help="Create a new backup")

    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument("file", help="Backup file to restore from")

    # List command
    subparsers.add_parser("list", help="List available backups")

    # Cleanup command
    subparsers.add_parser("cleanup", help="Remove old backups")

    args = parser.parse_args()

    if args.command == "backup":
        create_backup()
    elif args.command == "restore":
        restore_backup(args.file)
    elif args.command == "list":
        list_backups()
    elif args.command == "cleanup":
        cleanup_old_backups()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
