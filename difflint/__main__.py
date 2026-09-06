import argparse
import os
import sys
from typing import Iterable, Iterator, Optional

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


def format_finding(finding: Finding) -> str:
    return f'{finding.path}:{finding.line}: {finding.rule_id}: {finding.message}'


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
    args = parser.parse_args(argv)

    try:
        config = _resolve_config(args.config)
    except (ValueError, OSError) as exc:
        print(f'difflint: {exc}', file=sys.stderr)
        return 2

    found_any = False
    for finding in lint(parse_added_lines(_iter_source(args.patch)), rules=build_rules(config)):
        found_any = True
        print(format_finding(finding))

    return 1 if found_any else 0


if __name__ == '__main__':
    sys.exit(main())
