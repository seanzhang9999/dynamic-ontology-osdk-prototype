from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from .fixtures import (
    PROVIDER_FIELD_MAPPINGS,
    build_changchun_doir,
    build_power_doir,
    product_definitions,
)


class RegistryError(KeyError):
    pass


class DOIRRegistryLite:
    """Small SQLite-backed registry used by the v0.2 technical prototype.

    The registry makes fixtures an import/seed source instead of the compiler's
    direct dependency. It intentionally keeps the schema compact while exposing
    the same concepts a production registry would manage: ontology versions,
    product definitions, provider mappings, and compile artifacts.
    """

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._migrate()

    @classmethod
    def seeded(cls, *, coordinate_core: bool = False) -> "DOIRRegistryLite":
        registry = cls()
        registry.import_doir("enterprise-energy-credit", build_power_doir())
        registry.import_doir(
            "changchun-excavation-risk",
            build_changchun_doir(coordinate_core=coordinate_core),
        )
        for product_id, product in product_definitions().items():
            if product_id == "changchun-excavation-risk" and coordinate_core:
                product = dict(product)
                product["version"] = "1.1.0"
                product["ontology_version"] = "changchun-excavation-risk@1.1.0"
            registry.import_product(product_id, product)
        for mapping in PROVIDER_FIELD_MAPPINGS.values():
            registry.import_provider_mapping(mapping)
        return registry

    def _migrate(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS ontology_versions (
                product_id TEXT NOT NULL,
                ontology_version TEXT NOT NULL,
                status TEXT NOT NULL,
                doir_json TEXT NOT NULL,
                PRIMARY KEY (product_id, ontology_version)
            );
            CREATE TABLE IF NOT EXISTS product_versions (
                product_id TEXT NOT NULL,
                product_version TEXT NOT NULL,
                status TEXT NOT NULL,
                product_json TEXT NOT NULL,
                PRIMARY KEY (product_id, product_version)
            );
            CREATE TABLE IF NOT EXISTS provider_mappings (
                provider_id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                mapping_version TEXT NOT NULL,
                adapter TEXT NOT NULL,
                mapping_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS compile_artifacts (
                product_id TEXT NOT NULL,
                product_version TEXT NOT NULL,
                artifact_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (product_id, product_version)
            );
            """
        )
        self.conn.commit()

    def import_doir(self, product_id: str, doir: Dict[str, Any], status: str = "published") -> None:
        ontology = doir["ontology"]
        ontology_version = f"{ontology['id']}@{ontology['version']}"
        self.conn.execute(
            """
            INSERT OR REPLACE INTO ontology_versions
            (product_id, ontology_version, status, doir_json)
            VALUES (?, ?, ?, ?)
            """,
            (product_id, ontology_version, status, json.dumps(doir, ensure_ascii=False)),
        )
        self.conn.commit()

    def import_product(
        self, product_id: str, product: Dict[str, Any], status: str = "published"
    ) -> None:
        product_version = f"{product_id}@{product['version']}"
        self.conn.execute(
            """
            INSERT OR REPLACE INTO product_versions
            (product_id, product_version, status, product_json)
            VALUES (?, ?, ?, ?)
            """,
            (product_id, product_version, status, json.dumps(product, ensure_ascii=False)),
        )
        self.conn.commit()

    def import_provider_mapping(self, mapping: Dict[str, Any]) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO provider_mappings
            (provider_id, product_id, mapping_version, adapter, mapping_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                mapping["provider_id"],
                mapping["product_id"],
                mapping["mapping_version"],
                mapping["adapter"],
                json.dumps(mapping, ensure_ascii=False),
            ),
        )
        self.conn.commit()

    def get_doir(self, product_id: str, ontology_version: Optional[str] = None) -> Dict[str, Any]:
        if ontology_version:
            row = self.conn.execute(
                """
                SELECT doir_json FROM ontology_versions
                WHERE product_id = ? AND ontology_version = ?
                """,
                (product_id, ontology_version),
            ).fetchone()
        else:
            row = self.conn.execute(
                """
                SELECT doir_json FROM ontology_versions
                WHERE product_id = ? AND status = 'published'
                ORDER BY ontology_version DESC
                LIMIT 1
                """,
                (product_id,),
            ).fetchone()
        if not row:
            raise RegistryError(f"doir_not_found:{product_id}")
        return json.loads(row["doir_json"])

    def get_product(self, product_id: str, product_version: Optional[str] = None) -> Dict[str, Any]:
        if product_version:
            row = self.conn.execute(
                """
                SELECT product_json FROM product_versions
                WHERE product_id = ? AND product_version = ?
                """,
                (product_id, product_version),
            ).fetchone()
        else:
            row = self.conn.execute(
                """
                SELECT product_json FROM product_versions
                WHERE product_id = ? AND status = 'published'
                ORDER BY product_version DESC
                LIMIT 1
                """,
                (product_id,),
            ).fetchone()
        if not row:
            raise RegistryError(f"product_not_found:{product_id}")
        return json.loads(row["product_json"])

    def get_provider_mapping(self, provider_id: str) -> Dict[str, Any]:
        row = self.conn.execute(
            "SELECT mapping_json FROM provider_mappings WHERE provider_id = ?",
            (provider_id,),
        ).fetchone()
        if not row:
            raise RegistryError(f"provider_mapping_not_found:{provider_id}")
        return json.loads(row["mapping_json"])

    def list_provider_mappings(self) -> Dict[str, Dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT provider_id, mapping_json FROM provider_mappings ORDER BY provider_id"
        ).fetchall()
        return {row["provider_id"]: json.loads(row["mapping_json"]) for row in rows}

    def save_compile_artifact(
        self, product_id: str, product_version: str, artifact: Dict[str, Any]
    ) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO compile_artifacts
            (product_id, product_version, artifact_json)
            VALUES (?, ?, ?)
            """,
            (product_id, product_version, json.dumps(artifact, ensure_ascii=False)),
        )
        self.conn.commit()

    def state(self) -> Dict[str, Any]:
        ontologies = [
            dict(row)
            for row in self.conn.execute(
                "SELECT product_id, ontology_version, status FROM ontology_versions"
            ).fetchall()
        ]
        products = [
            dict(row)
            for row in self.conn.execute(
                "SELECT product_id, product_version, status FROM product_versions"
            ).fetchall()
        ]
        mappings = [
            {
                "provider_id": row["provider_id"],
                "product_id": row["product_id"],
                "mapping_version": row["mapping_version"],
                "adapter": row["adapter"],
            }
            for row in self.conn.execute(
                "SELECT provider_id, product_id, mapping_version, adapter FROM provider_mappings"
            ).fetchall()
        ]
        return {
            "ontology_versions": ontologies,
            "product_versions": products,
            "provider_mappings": mappings,
        }
