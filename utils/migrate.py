from __future__ import annotations

import argparse
import asyncio
import importlib
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from database import get_collection, get_database

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def _discover_migrations() -> list[dict[str, Any]]:
    migrations: list[dict[str, Any]] = []
    for path in sorted(MIGRATIONS_DIR.glob("[0-9]*.py")):
        name = path.stem
        parts = name.split("_", 1)
        try:
            version = int(parts[0])
        except ValueError:
            continue
        description = parts[1].replace("_", " ").title() if len(parts) > 1 else "Sin descripción"
        migrations.append(
            {
                "version": version,
                "name": name,
                "description": description,
            }
        )
    return migrations


async def get_current_version() -> int:
    col = await get_collection("_migrations")
    doc = await col.find_one(sort=[("version", -1)])
    return doc["version"] if doc else 0


async def get_pending() -> list[dict[str, Any]]:
    current = await get_current_version()
    all_migs = _discover_migrations()
    return [m for m in all_migs if m["version"] > current]


async def apply_pending() -> list[int]:
    pending = await get_pending()
    if not pending:
        logger.info("No hay migraciones pendientes")
        return []

    db = await get_database()
    col = await get_collection("_migrations")
    applied: list[int] = []

    for mig in sorted(pending, key=lambda x: x["version"]):
        logger.info("Aplicando migración %d: %s", mig["version"], mig["description"])
        try:
            module = importlib.import_module(f"migrations.{mig['name']}")
            await module.up(db)
            await col.insert_one(
                {
                    "version": mig["version"],
                    "description": mig["description"],
                    "applied_at": datetime.now(UTC),
                }
            )
            logger.info("Migración %d aplicada correctamente", mig["version"])
            applied.append(mig["version"])
        except Exception:
            logger.exception("Error aplicando migración %d", mig["version"])
            raise

    return applied


async def rollback(steps: int = 1) -> list[int]:
    col = await get_collection("_migrations")
    db = await get_database()
    last = await col.find_one(sort=[("version", -1)])
    if not last:
        logger.info("No hay migraciones para revertir")
        return []

    target = last["version"] - steps
    rolled_back: list[int] = []

    cursor = col.find(
        {"version": {"$gt": target}},
        sort=[("version", -1)],
    )
    async for doc in cursor:
        version = doc["version"]
        migs = _discover_migrations()
        match = [m for m in migs if m["version"] == version]
        if not match:
            logger.warning("No se encontró script para migración %d, saltando", version)
            continue
        mig = match[0]
        logger.info("Revirtiendo migración %d: %s", version, mig["description"])
        try:
            module = importlib.import_module(f"migrations.{mig['name']}")
            await module.down(db)
            await col.delete_one({"version": version})
            logger.info("Migración %d revertida", version)
            rolled_back.append(version)
        except Exception:
            logger.exception("Error revirtiendo migración %d", version)
            raise

    return rolled_back


async def status() -> list[dict[str, Any]]:
    col = await get_collection("_migrations")
    applied_cursor = col.find(sort=[("version", 1)])
    applied_map: dict[int, datetime] = {}
    async for doc in applied_cursor:
        applied_map[doc["version"]] = doc["applied_at"]

    result: list[dict[str, Any]] = []
    for mig in _discover_migrations():
        result.append(
            {
                "version": mig["version"],
                "description": mig["description"],
                "applied": mig["version"] in applied_map,
                "applied_at": applied_map.get(mig["version"]),
            }
        )
    return result


async def _cmd_upgrade() -> None:
    applied = await apply_pending()
    if applied:
        logger.info(f"Migraciones aplicadas: {applied}")
    else:
        logger.info("Todo actualizado")


async def _cmd_downgrade(steps: int) -> None:
    rolled = await rollback(steps)
    if rolled:
        logger.info(f"Migraciones revertidas: {rolled}")
    else:
        logger.info("Nada que revertir")


async def _cmd_status() -> None:
    rows = await status()
    if not rows:
        logger.info("No hay migraciones definidas")
        return
    logger.info(f"{'Versión':<10} {'Aplicada':<10} {'Descripción'}")
    logger.info("-" * 60)
    for row in rows:
        applied = "SI" if row["applied"] else "NO"
        logger.info(f"{row['version']:<10} {applied:<10} {row['description']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gestor de migraciones MongoDB")
    parser.add_argument("command", nargs="?", choices=["upgrade", "downgrade", "status", "rollback"], default="status")
    parser.add_argument("--steps", type=int, default=1, help="Pasos a revertir (default: 1)")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if args.command == "upgrade":
        asyncio.run(_cmd_upgrade())
    elif args.command in ("downgrade", "rollback"):
        asyncio.run(_cmd_downgrade(args.steps))
    else:
        asyncio.run(_cmd_status())


if __name__ == "__main__":
    main()
