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


def make_line_length_rule(max_length: int = MAX_LINE_LENGTH) -> Callable[[AddedLine], List[Finding]]:
    """Build a line-length rule bound to `max_length`.

    A factory rather than a single function because the config file lets
    a caller pick their own limit; `check_line_length` below is just this
    factory called with the default, kept as a name for anyone importing
    it directly.
    """
    def check_line_length(added: AddedLine) -> List[Finding]:
        if len(added.text) > max_length:
            return [Finding(added.path, added.lineno, 'line-too-long',
                             f'line is {len(added.text)} chars, over {max_length}')]
        return []
    return check_line_length


check_line_length = make_line_length_rule(MAX_LINE_LENGTH)


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


def check_trailing_blank_line(added: AddedLine) -> List[Finding]:
    # Unlike the other rules, `is_trailing_blank` isn't computed from this
    # line alone - the parser only sets it once it has confirmed no context
    # line, later hunk, or later file section follows this one.
    if added.is_trailing_blank:
        return [Finding(added.path, added.lineno, 'trailing-blank-line',
                         'blank line added at the end of the file')]
    return []


RULE_IDS = frozenset({
    'trailing-whitespace',
    'hard-tab',
    'line-too-long',
    'conflict-marker',
    'trailing-blank-line',
})

DEFAULT_RULES: List[Callable[[AddedLine], List[Finding]]] = [
    check_trailing_whitespace,
    check_line_length,
    check_hard_tab,
    check_conflict_marker,
    check_trailing_blank_line,
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
