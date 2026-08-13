"""The committed data dictionary has to match the models.

Documentation that describes the schema as it was six months ago is worse than
none: a reader trusts it and cannot tell it is wrong. `docs/data-dictionary.md`
is generated from `Base.metadata`, and this test is what stops it drifting —
add a column without regenerating and the build goes red.
"""

import pytest

from app.scripts.data_dictionary import OUTPUT_PATH, render

REGENERATE = "docker compose run --rm --no-deps test python -m app.scripts.data_dictionary"


def test_the_committed_document_matches_the_models() -> None:
    if not OUTPUT_PATH.exists():
        pytest.fail(f"{OUTPUT_PATH} is missing. Generate it with:\n    {REGENERATE}")

    committed = OUTPUT_PATH.read_text(encoding="utf-8")
    current = render()

    assert committed == current, (
        f"{OUTPUT_PATH.name} no longer matches the models. Regenerate it with:\n    {REGENERATE}"
    )


def test_every_table_is_documented() -> None:
    """A table nobody wrote down is a table nobody knows the rules of."""
    from app.db.base import Base

    document = render()
    for name in Base.metadata.tables:
        assert f"### `{name}`" in document, f"{name} is missing from the data dictionary"
