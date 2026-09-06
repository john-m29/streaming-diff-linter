"""Config file support: enable/disable rules and set the max line length.

The format is a minimal INI file, read with `configparser` from the
standard library:

    [difflint]
    max-line-length = 100
    disable = hard-tab, conflict-marker

Every rule runs unless its id is listed under `disable`. `max-line-length`
only affects the `line-too-long` rule; the others don't take options yet.
"""

import configparser
from dataclasses import dataclass, field
from typing import Callable, FrozenSet, List

from .parser import AddedLine
from .rules import (
    RULE_IDS,
    Finding,
    check_conflict_marker,
    check_hard_tab,
    check_trailing_whitespace,
    make_line_length_rule,
)
from .rules import MAX_LINE_LENGTH as DEFAULT_MAX_LINE_LENGTH

SECTION = 'difflint'


@dataclass(frozen=True)
class Config:
    max_line_length: int = DEFAULT_MAX_LINE_LENGTH
    disabled_rules: FrozenSet[str] = field(default_factory=frozenset)


def load_config(path: str) -> Config:
    """Read a difflint config file.

    Raises `ValueError` if the file names a rule id that doesn't exist, so
    a typo in `disable = ` fails loudly instead of silently linting with
    every rule still on.
    """
    parser = configparser.ConfigParser()
    with open(path, 'r', encoding='utf-8') as handle:
        parser.read_file(handle)

    if not parser.has_section(SECTION):
        return Config()

    section = parser[SECTION]
    max_line_length = section.getint('max-line-length', fallback=DEFAULT_MAX_LINE_LENGTH)
    disabled = frozenset(
        name.strip() for name in section.get('disable', fallback='').split(',') if name.strip()
    )

    unknown = disabled - RULE_IDS
    if unknown:
        raise ValueError(f"unknown rule id(s) in {path}: {', '.join(sorted(unknown))}")

    return Config(max_line_length=max_line_length, disabled_rules=disabled)


def build_rules(config: Config) -> List[Callable[[AddedLine], List[Finding]]]:
    """Turn a `Config` into the ordered list of rules `lint()` should run."""
    candidates = [
        ('trailing-whitespace', check_trailing_whitespace),
        ('line-too-long', make_line_length_rule(config.max_line_length)),
        ('hard-tab', check_hard_tab),
        ('conflict-marker', check_conflict_marker),
    ]
    return [rule for rule_id, rule in candidates if rule_id not in config.disabled_rules]
