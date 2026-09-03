"""Streaming parser for unified diffs.

The only thing this module cares about is: for each line a diff adds, what
file did it land in and what line number does it have in the new version of
that file. It does not try to understand hunks fully (old-side line numbers,
renames, binary markers) beyond what's needed to keep that count straight.
"""

import re
from dataclasses import dataclass
from typing import Iterable, Iterator, Optional

HUNK_HEADER_RE = re.compile(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@')


@dataclass(frozen=True)
class AddedLine:
    path: str
    lineno: int
    text: str


def _parse_new_path(header_line: str) -> Optional[str]:
    # "+++ b/some/path.py" or "+++ b/some/path.py\t2024-01-01 ..." or
    # "+++ /dev/null" for a deleted file.
    rest = header_line[len('+++ '):].rstrip('\n')
    rest = rest.split('\t', 1)[0]
    if rest == '/dev/null':
        return None
    if rest.startswith('b/'):
        rest = rest[2:]
    return rest


def parse_added_lines(lines: Iterable[str]) -> Iterator[AddedLine]:
    """Walk a unified diff and yield each added line with its position in
    the new file.

    `lines` is consumed one line at a time and nothing is buffered beyond
    the current line and a handful of counters, so this is safe to point at
    a `subprocess.PIPE` or an open file for a patch far larger than memory.
    """
    current_path: Optional[str] = None
    new_lineno = 0
    in_hunk = False

    for raw in lines:
        if raw.startswith('+++ '):
            current_path = _parse_new_path(raw)
            in_hunk = False
            continue
        if raw.startswith('--- ') or raw.startswith('diff --git') or raw.startswith('index '):
            in_hunk = False
            continue

        match = HUNK_HEADER_RE.match(raw)
        if match:
            new_lineno = int(match.group(1))
            in_hunk = True
            continue

        if not in_hunk or current_path is None:
            continue

        if raw.startswith('\\'):
            # "\ No newline at end of file" - marker, not a real line.
            continue
        if raw.startswith('+'):
            yield AddedLine(current_path, new_lineno, raw[1:].rstrip('\n'))
            new_lineno += 1
        elif raw.startswith('-'):
            pass
        elif raw.startswith(' ') or raw in ('\n', ''):
            new_lineno += 1
        else:
            # Something inside what we thought was a hunk that isn't a
            # +/-/context line. Rather than guess, stop trusting line
            # numbers until the next hunk header resets them.
            in_hunk = False
