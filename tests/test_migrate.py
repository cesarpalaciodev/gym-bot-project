from __future__ import annotations

from unittest.mock import patch

from utils.migrate import _discover_migrations


class TestDiscoverMigrations:
    def test_discovers_migration_001(self) -> None:
        migrations = _discover_migrations()
        versions = [m["version"] for m in migrations]
        assert 1 in versions

    def test_migration_001_metadata(self) -> None:
        migrations = _discover_migrations()
        m001 = next((m for m in migrations if m["version"] == 1), None)
        assert m001 is not None
        assert m001["description"] == "Create Initial Schema"
        assert m001["name"] == "001_create_initial_schema"

    def test_migrations_sorted_by_version(self) -> None:
        migrations = _discover_migrations()
        versions = [m["version"] for m in migrations]
        assert versions == sorted(versions)

    def test_empty_when_no_migration_dir(self, tmp_path: str) -> None:
        with patch("utils.migrate.MIGRATIONS_DIR", tmp_path):  # type: ignore[assignment]
            result = _discover_migrations()
        assert result == []

    def test_skips_non_numeric_prefix(self, tmp_path: str) -> None:
        d = tmp_path / "migrations"
        d.mkdir()
        (d / "foo_bar.py").write_text("")
        with patch("utils.migrate.MIGRATIONS_DIR", d):
            result = _discover_migrations()
        assert result == []

    def test_handles_version_without_description(self, tmp_path: str) -> None:
        d = tmp_path / "migrations"
        d.mkdir()
        (d / "42.py").write_text("")
        with patch("utils.migrate.MIGRATIONS_DIR", d):
            result = _discover_migrations()
        assert len(result) == 1
        assert result[0]["version"] == 42
        assert result[0]["description"] == "Sin descripción"
