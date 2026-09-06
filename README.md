# difflint

Code review tools mostly lint the *files*, not the *diff*. That means a
five-year-old file full of long lines and stray tabs gets flagged on every
pull request even though the PR only touched three lines of it. difflint
only looks at the lines a diff actually adds, and reports them with the
line number they land on in the new version of the file - the number your
editor and `git blame` will show you, not an offset into the patch.

It reads a unified diff (the output of `git diff`, `git show`, or a `.patch`
file) and runs a small set of checks against every added line: trailing
whitespace, hard tabs, lines that are too long, and leftover merge conflict
markers.

## Why streaming matters here

Patches can be huge - a vendored dependency bump, a generated file, a
rebase that touched half the repo. difflint never reads the diff into a
single string or list. It iterates the input line by line (a file object,
or `sys.stdin`, is already a lazy line iterator) and keeps only a handful
of counters as state: the current file path and the current line number.
Memory use stays flat whether the patch is 40 lines or 4 million.

## Usage

Lint a diff piped in from git:

```
git diff | python -m difflint
```

Lint a saved patch file:

```
python -m difflint some_change.patch
```

Example output:

```
src/app.py:42: trailing-whitespace: line has trailing whitespace
src/app.py:57: line-too-long: line is 134 chars, over 100
src/app.py:103: conflict-marker: line looks like an unresolved merge conflict marker
```

Exit status is `1` if any findings were reported, `0` otherwise, so it
plugs into a CI step or a pre-push hook:

```
git diff --cached | python -m difflint || echo "fix the above before committing"
```

## Using it as a library

```python
from difflint import parse_added_lines, lint

with open("some_change.patch") as patch:
    for finding in lint(parse_added_lines(patch)):
        print(finding.path, finding.line, finding.rule_id, finding.message)
```

`parse_added_lines` is a generator over `AddedLine(path, lineno, text)`.
`lint` is a generator over `Finding(path, line, rule_id, message)`. Neither
buffers more than the current line, so you can chain them directly onto an
open file or a subprocess pipe.

## Rules

| id | what it flags |
|----|----------------|
| `trailing-whitespace` | added line ends with whitespace |
| `hard-tab` | added line contains a tab character |
| `line-too-long` | added line is over 100 characters (configurable) |
| `conflict-marker` | added line looks like `<<<<<<<`, `=======`, or `>>>>>>>` |

## Config file

By default difflint reads `.difflintrc` from the current directory if one
exists. Point it at a different file with `--config`:

```
git diff | python -m difflint --config ci/difflint.ini
```

It's a small INI file under a `[difflint]` section:

```ini
[difflint]
max-line-length = 120
disable = hard-tab, conflict-marker
```

`disable` is a comma-separated list of rule ids from the table above. An
unknown rule id in `disable` is an error, not a silent no-op. Without a
config file, all rules run with `max-line-length = 100`.

## Status

No packaged tests yet. See the roadmap in the project notes for what's
next.

## Requirements

Python 3.8+, standard library only.
