"""Generate `docs/data-dictionary.md` from the SQLAlchemy models.

Written rather than hand-maintained on purpose. A data dictionary that is typed
out by hand is accurate on the day it is written and misleading a month later,
and a reader has no way to tell which day they are looking at. This one is
derived from `Base.metadata`, and `tests/test_data_dictionary.py` fails if the
committed file no longer matches the models — so it is either current or the
build is red.

Usage:
    python -m app.scripts.data_dictionary          # write docs/data-dictionary.md
    python -m app.scripts.data_dictionary --stdout # print it instead
"""

import sys
from pathlib import Path

from sqlalchemy import Column, Enum, Table
from sqlalchemy.dialects import postgresql

import app.models  # noqa: F401  (imported for its side effect: registers every table)
from app.db.base import Base

REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_PATH = REPO_ROOT / "docs" / "data-dictionary.md"

HEADER = """<!--
GENERATED FILE — do not edit by hand.

Regenerate with:
    docker compose run --rm --no-deps test python -m app.scripts.data_dictionary

`tests/test_data_dictionary.py` fails when this file and the models disagree.
-->

# Veri Sözlüğü

Şema `backend/app/models/` altındaki SQLAlchemy modellerinden üretilir; tabloları
veritabanına uygulayan zincir `backend/alembic/versions/` içindedir.
"""


PG = postgresql.dialect()  # type: ignore[no-untyped-call]


def _type_of(column: Column[object]) -> str:
    """The type as PostgreSQL sees it, not SQLAlchemy's generic name.

    `str(column.type)` renders a timestamptz as `DATETIME`, which is not a
    thing anybody will find in the database.
    """
    if isinstance(column.type, Enum):
        # The labels stored in the column are the Python enum *names*; the API
        # speaks the values (`booking.created`).
        return f"ENUM({', '.join(column.type.enums)})"
    return str(column.type.compile(dialect=PG))


def _default_of(column: Column[object]) -> str:
    if column.identity is not None:
        return "`IDENTITY`"
    if column.server_default is not None:
        arg = getattr(column.server_default, "arg", None)
        text = getattr(arg, "text", None) or str(arg)
        return f"`{text}`"
    if column.default is not None:
        # Client-side: SQLAlchemy fills it in on flush, so a row written by
        # anything other than this application will not get it.
        arg = getattr(column.default, "arg", None)
        name = getattr(arg, "__name__", None) or str(arg)
        return f"`{name}` (uygulama)"
    return "—"


def _notes_of(table: Table, column: Column[object]) -> str:
    notes: list[str] = []
    if column.primary_key:
        notes.append("PK")
    for key in column.foreign_keys:
        notes.append(f"FK → `{key.column.table.name}.{key.column.name}`")
        if key.ondelete:
            notes.append(f"ON DELETE {key.ondelete}")
    if column.unique:
        notes.append("benzersiz")
    # `index=True` on the column and a table-level `Index(...)` both end up as
    # an index on the column; the reader does not care which way it was spelt.
    indexed = column.index or any(
        len(index.columns) == 1 and column.name in index.columns for index in table.indexes
    )
    if indexed:
        notes.append("indeksli")
    return ", ".join(notes) or "—"


def _describe(table: Table) -> str:
    """The model class docstring, if the table has a mapped class."""
    for mapper in Base.registry.mappers:
        if mapper.local_table is table:
            doc = (mapper.class_.__doc__ or "").strip()
            return doc.split("\n")[0] if doc else ""
    return ""


def _diagram(tables: list[Table]) -> str:
    lines = ["```mermaid", "erDiagram"]
    seen: set[tuple[str, str, str]] = set()
    for table in tables:
        for column in table.columns:
            for key in column.foreign_keys:
                parent = key.column.table.name
                edge = (parent, table.name, column.name)
                if edge in seen:
                    continue
                seen.add(edge)
                # One parent row, many children. Optional on the child side when
                # the column is nullable.
                cardinality = "||--o{" if not column.nullable else "||--o|"
                lines.append(f"    {parent} {cardinality} {table.name} : {column.name}")
    for table in tables:
        if not any(table.name in edge[:2] for edge in seen):
            # Standalone tables would otherwise be missing from the picture.
            lines.append(f"    {table.name} {{")
            lines.append("    }")
    lines.append("```")
    return "\n".join(lines)


def render() -> str:
    tables = sorted(Base.metadata.tables.values(), key=lambda t: t.name)

    parts = [HEADER, "\n## Tablo ilişkileri\n\n", _diagram(tables), "\n\n## Tablolar\n"]

    for table in tables:
        parts.append(f"\n### `{table.name}`\n")
        description = _describe(table)
        if description:
            parts.append(f"\n{description}\n")
        parts.append("\n| Sütun | Tip | Boş geçilebilir | Varsayılan | Notlar |")
        parts.append("\n| --- | --- | --- | --- | --- |")
        for column in table.columns:
            parts.append(
                f"\n| `{column.name}` | {_type_of(column)} | "
                f"{'evet' if column.nullable else 'hayır'} | "
                f"{_default_of(column)} | {_notes_of(table, column)} |"
            )
        parts.append("\n")

    return "".join(parts).rstrip() + "\n"


def main() -> None:
    document = render()
    if "--stdout" in sys.argv:
        sys.stdout.write(document)
        return
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(document, encoding="utf-8", newline="\n")
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
