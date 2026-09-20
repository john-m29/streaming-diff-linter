import json
import unittest

from difflint.__main__ import format_finding_json, format_finding_text
from difflint.rules import Finding


class FormatFindingTests(unittest.TestCase):
    def setUp(self):
        self.finding = Finding('src/app.py', 42, 'hard-tab', 'line contains a hard tab')

    def test_text_format(self):
        self.assertEqual(
            format_finding_text(self.finding),
            'src/app.py:42: hard-tab: line contains a hard tab',
        )

    def test_json_format_round_trips(self):
        decoded = json.loads(format_finding_json(self.finding))
        self.assertEqual(decoded, {
            'path': 'src/app.py',
            'line': 42,
            'rule_id': 'hard-tab',
            'message': 'line contains a hard tab',
        })

    def test_json_format_is_one_line(self):
        # json output has to stay streamable: one finding, one line.
        self.assertNotIn('\n', format_finding_json(self.finding))


if __name__ == '__main__':
    unittest.main()
