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
    # True only once we've seen what comes after this line in the diff and
    # confirmed nothing else follows it in the new file: no context line,
    # no later hunk, no next file section. Set by parse_added_lines, which
    # holds a blank added line back until that's known.
    is_trailing_blank: bool = False


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
    the current line, a handful of counters, and (only while a run of blank
    added lines might still turn out to be at end of file) that short run
    itself - so this is safe to point at a `subprocess.PIPE` or an open
    file for a patch far larger than memory.
    """
    current_path: Optional[str] = None
    new_lineno = 0
    in_hunk = False
    # A blank added line might be the last line of the new file, or it
    # might just be a blank line with more content after it - we can't
    # tell until we see whether a context line, another hunk, or another
    # file section follows. Hold it here until that's resolved.
    pending_blanks = []

    def release(trailing):
        for path, lineno, text in pending_blanks:
            yield AddedLine(path, lineno, text, is_trailing_blank=trailing)
        pending_blanks.clear()

    for raw in lines:
        if raw.startswith('+++ '):
            yield from release(True)
            current_path = _parse_new_path(raw)
            in_hunk = False
            continue
        if raw.startswith('--- ') or raw.startswith('diff --git') or raw.startswith('index '):
            yield from release(True)
            in_hunk = False
            continue

        match = HUNK_HEADER_RE.match(raw)
        if match:
            # A later hunk for the same file means there's more of the
            # file after this point, so anything pending wasn't trailing.
            yield from release(False)
            new_lineno = int(match.group(1))
            in_hunk = True
            continue

        if not in_hunk or current_path is None:
            continue

        if raw.startswith('\\'):
            # "\ No newline at end of file" - marker, not a real line.
            continue
        if raw.startswith('+'):
            text = raw[1:].rstrip('\n')
            if text.strip() == '':
                pending_blanks.append((current_path, new_lineno, text))
            else:
                yield from release(False)
                yield AddedLine(current_path, new_lineno, text)
            new_lineno += 1
        elif raw.startswith('-'):
            pass
        elif raw.startswith(' ') or raw in ('\n', ''):
            yield from release(False)
            new_lineno += 1
        else:
            # Something inside what we thought was a hunk that isn't a
            # +/-/context line. Rather than guess, stop trusting line
            # numbers until the next hunk header resets them.
            yield from release(False)
            in_hunk = False

    yield from release(True)
