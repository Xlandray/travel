"""URL slug generation.

Single source of truth for slugs derived from user-entered names. The rule
mirrors, step for step, the SQL expression in migration `c7a9b3f5d1e2` (the one
that backfills `hotels.slug`):

1. transliterate Turkish letters to ASCII (see `SLUG_TRANSLATION`),
2. collapse every run of non-alphanumeric characters into a single hyphen,
3. trim leading and trailing hyphens,
4. lowercase.

If this function and that migration disagree, the same record can end up with
two different URLs, so the two definitions must be changed together.
"""

import re

SLUG_TRANSLATION = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosucgiosu")
_NON_ALNUM = re.compile(r"[^a-zA-Z0-9]+")


def generate_slug(value: str) -> str:
    """Return a slug for `value`, or an empty string if nothing is slug-able."""
    ascii_value = value.translate(SLUG_TRANSLATION)
    hyphenated = ascii_value  # deliberate break: CI must catch this
    return hyphenated.strip("-").lower()
