import unittest

from difflint.parser import AddedLine, parse_added_lines
from difflint.rules import (
    DEFAULT_RULES,
    check_conflict_marker,
    check_hard_tab,
    check_line_length,
    check_trailing_whitespace,
    lint,
    make_line_length_rule,
)
from tests.test_parser import SINGLE_FILE_DIFF


def added(text, path='f.py', lineno=1):
    return AddedLine(path, lineno, text)


class TrailingWhitespaceTests(unittest.TestCase):
    def test_flags_trailing_spaces(self):
        findings = check_trailing_whitespace(added('x = 1   '))
        self.assertEqual([f.rule_id for f in findings], ['trailing-whitespace'])

    def test_ignores_clean_line(self):
        self.assertEqual(check_trailing_whitespace(added('x = 1')), [])

    def test_ignores_whitespace_only_line(self):
        # A blank line that's pure whitespace isn't "trailing" whitespace on
        # content, so this rule leaves it alone.
        self.assertEqual(check_trailing_whitespace(added('    ')), [])


class LineLengthTests(unittest.TestCase):
    def test_flags_line_over_default_limit(self):
        findings = check_line_length(added('a' * 101))
        self.assertEqual([f.rule_id for f in findings], ['line-too-long'])

    def test_allows_line_at_limit(self):
        self.assertEqual(check_line_length(added('a' * 100)), [])

    def test_custom_limit(self):
        rule = make_line_length_rule(10)
        self.assertEqual(rule(added('a' * 10)), [])
        self.assertEqual(len(rule(added('a' * 11))), 1)


class HardTabTests(unittest.TestCase):
    def test_flags_tab(self):
        findings = check_hard_tab(added('\tx = 1'))
        self.assertEqual([f.rule_id for f in findings], ['hard-tab'])

    def test_ignores_spaces(self):
        self.assertEqual(check_hard_tab(added('    x = 1')), [])


class ConflictMarkerTests(unittest.TestCase):
    def test_flags_start_marker(self):
        findings = check_conflict_marker(added('<<<<<<< HEAD'))
        self.assertEqual([f.rule_id for f in findings], ['conflict-marker'])

    def test_flags_end_marker(self):
        findings = check_conflict_marker(added('>>>>>>> feature-branch'))
        self.assertEqual([f.rule_id for f in findings], ['conflict-marker'])

    def test_flags_separator(self):
        findings = check_conflict_marker(added('======='))
        self.assertEqual([f.rule_id for f in findings], ['conflict-marker'])

    def test_ignores_unrelated_equals_run(self):
        self.assertEqual(check_conflict_marker(added('a = b == c')), [])


class LintTests(unittest.TestCase):
    def test_runs_default_rules_over_a_real_diff(self):
        findings = list(lint(parse_added_lines(SINGLE_FILE_DIFF)))

        self.assertEqual(
            [(f.line, f.rule_id) for f in findings],
            [(13, 'trailing-whitespace'), (16, 'hard-tab')],
        )

    def test_only_runs_the_rules_it_is_given(self):
        findings = list(lint([added('\tx   ')], rules=[check_hard_tab]))
        self.assertEqual([f.rule_id for f in findings], ['hard-tab'])

    def test_default_rules_constant_matches_available_rules(self):
        self.assertEqual(len(DEFAULT_RULES), 4)


if __name__ == '__main__':
    unittest.main()
