"""Checks that run against each added line.

A rule is any callable that takes an `AddedLine` and returns a list of
`Finding`s (usually zero or one). Keeping them as plain functions instead of
a class hierarchy means adding a new check is one function plus one entry in
DEFAULT_RULES.
"""

from dataclasses import dataclass
from typing import Callable, Iterable, Iterator, List, Optional

from .parser import AddedLine

MAX_LINE_LENGTH = 100


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    rule_id: str
    message: str


def check_trailing_whitespace(added: AddedLine) -> List[Finding]:
    if added.text.strip() and added.text != added.text.rstrip():
        return [Finding(added.path, added.lineno, 'trailing-whitespace',
                         'line has trailing whitespace')]
    return []


def check_line_length(added: AddedLine) -> List[Finding]:
    if len(added.text) > MAX_LINE_LENGTH:
        return [Finding(added.path, added.lineno, 'line-too-long',
                         f'line is {len(added.text)} chars, over {MAX_LINE_LENGTH}')]
    return []


def check_hard_tab(added: AddedLine) -> List[Finding]:
    if '\t' in added.text:
        return [Finding(added.path, added.lineno, 'hard-tab',
                         'line contains a hard tab')]
    return []


def check_conflict_marker(added: AddedLine) -> List[Finding]:
    stripped = added.text.strip()
    if stripped.startswith('<<<<<<<') or stripped.startswith('>>>>>>>') or stripped == '=======':
        return [Finding(added.path, added.lineno, 'conflict-marker',
                         'line looks like an unresolved merge conflict marker')]
    return []


DEFAULT_RULES: List[Callable[[AddedLine], List[Finding]]] = [
    check_trailing_whitespace,
    check_line_length,
    check_hard_tab,
    check_conflict_marker,
]


def lint(added_lines: Iterable[AddedLine],
         rules: Optional[List[Callable[[AddedLine], List[Finding]]]] = None) -> Iterator[Finding]:
    """Run `rules` over `added_lines`, yielding findings as they're found.

    Both this and `added_lines` are generators end to end, so a caller can
    start printing findings before the diff has finished streaming in.
    """
    active_rules = rules if rules is not None else DEFAULT_RULES
    for added in added_lines:
        for rule in active_rules:
            for finding in rule(added):
                yield finding
