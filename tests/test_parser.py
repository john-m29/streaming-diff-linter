import unittest

from difflint.parser import parse_added_lines

# Built line by line (rather than one literal block) so the trailing
# whitespace on the "another new line" entry survives editors/formatters
# that would otherwise strip it on save.
SINGLE_FILE_DIFF = [
    'diff --git a/src/app.py b/src/app.py\n',
    'index 1234567..89abcde 100644\n',
    '--- a/src/app.py\n',
    '+++ b/src/app.py\n',
    '@@ -10,6 +10,8 @@ def foo():\n',
    ' line one\n',
    ' line two\n',
    '-old line\n',
    '+new line\n',
    '+another new line' + '   ' + '\n',
    ' line three\n',
    ' line four\n',
    '+' + '\t' + 'tabbed line\n',
]

MULTI_FILE_DIFF = [
    'diff --git a/a.txt b/a.txt\n',
    'index 1111111..2222222 100644\n',
    '--- a/a.txt\n',
    '+++ b/a.txt\n',
    '@@ -1,2 +1,2 @@\n',
    '-old a\n',
    '+new a\n',
    ' context a\n',
    'diff --git a/gone.txt b/gone.txt\n',
    'deleted file mode 100644\n',
    'index 3333333..0000000\n',
    '--- a/gone.txt\n',
    '+++ /dev/null\n',
    '@@ -1,2 +0,0 @@\n',
    '-line one\n',
    '-line two\n',
    'diff --git a/b.txt b/b.txt\n',
    'index 4444444..5555555 100644\n',
    '--- a/b.txt\n',
    '+++ b/b.txt\n',
    '@@ -5,2 +5,3 @@\n',
    ' context b\n',
    '+new b\n',
    ' context b2\n',
]


class ParseAddedLinesTests(unittest.TestCase):
    def test_new_file_line_numbers_account_for_context_and_deletions(self):
        added = list(parse_added_lines(SINGLE_FILE_DIFF))

        self.assertEqual(
            [(a.path, a.lineno, a.text) for a in added],
            [
                ('src/app.py', 12, 'new line'),
                ('src/app.py', 13, 'another new line   '),
                ('src/app.py', 16, '\ttabbed line'),
            ],
        )

    def test_switches_path_per_file_and_skips_deleted_files(self):
        added = list(parse_added_lines(MULTI_FILE_DIFF))

        self.assertEqual(
            [(a.path, a.lineno, a.text) for a in added],
            [
                ('a.txt', 1, 'new a'),
                ('b.txt', 6, 'new b'),
            ],
        )

    def test_lines_outside_any_hunk_are_ignored(self):
        diff = [
            '+++ b/README.md\n',
            'not a hunk yet\n',
            '@@ -1,1 +1,1 @@\n',
            '+hello\n',
        ]
        added = list(parse_added_lines(diff))
        self.assertEqual([(a.path, a.lineno, a.text) for a in added], [('README.md', 1, 'hello')])


if __name__ == '__main__':
    unittest.main()
