import argparse
import json
import os
import sys
from typing import Callable, Dict, Iterable, Iterator, Optional

from .config import Config, build_rules, load_config
from .parser import parse_added_lines
from .rules import Finding, lint

DEFAULT_CONFIG_FILENAME = '.difflintrc'


def _resolve_config(explicit_path: Optional[str]) -> Config:
    if explicit_path:
        return load_config(explicit_path)
    if os.path.isfile(DEFAULT_CONFIG_FILENAME):
        return load_config(DEFAULT_CONFIG_FILENAME)
    return Config()


def _iter_source(path: str) -> Iterator[str]:
    if path == '-':
        for line in sys.stdin:
            yield line
        return
    with open(path, 'r', encoding='utf-8', errors='replace') as handle:
        for line in handle:
            yield line


def format_finding_text(finding: Finding) -> str:
    return f'{finding.path}:{finding.line}: {finding.rule_id}: {finding.message}'


def format_finding_json(finding: Finding) -> str:
    # One object per line (JSON Lines) rather than a wrapping array, so
    # output can still be printed finding-by-finding as the diff streams in
    # instead of buffering until everything has been read.
    return json.dumps({
        'path': finding.path,
        'line': finding.line,
        'rule_id': finding.rule_id,
        'message': finding.message,
    })


FORMATTERS: Dict[str, Callable[[Finding], str]] = {
    'text': format_finding_text,
    'json': format_finding_json,
}


def main(argv: Iterable[str] = None) -> int:
    parser = argparse.ArgumentParser(
        prog='difflint',
        description='Lint the lines a unified diff adds, without loading the whole patch into memory.',
    )
    parser.add_argument('patch', nargs='?', default='-',
                         help='path to a diff/patch file, or - to read from stdin (default)')
    parser.add_argument('--config',
                         help='path to a difflint config file '
                              f'(default: {DEFAULT_CONFIG_FILENAME} in the current directory, if present)')
    parser.add_argument('--format', choices=sorted(FORMATTERS), default='text',
                         help='output format: "text" (default) or "json" (one finding per line)')
    args = parser.parse_args(argv)

    try:
        config = _resolve_config(args.config)
    except (ValueError, OSError) as exc:
        print(f'difflint: {exc}', file=sys.stderr)
        return 2

    format_finding = FORMATTERS[args.format]

    found_any = False
    for finding in lint(parse_added_lines(_iter_source(args.patch)), rules=build_rules(config)):
        found_any = True
        print(format_finding(finding))

    return 1 if found_any else 0


if __name__ == '__main__':
    sys.exit(main())
