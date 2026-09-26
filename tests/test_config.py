import os
import tempfile
import unittest

from difflint.config import Config, build_rules, load_config


def write_config(tmpdir, contents):
    path = os.path.join(tmpdir, '.difflintrc')
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write(contents)
    return path


class LoadConfigTests(unittest.TestCase):
    def test_missing_section_falls_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_config(tmpdir, '[other-tool]\nfoo = bar\n')
            self.assertEqual(load_config(path), Config())

    def test_reads_max_line_length_and_disabled_rules(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_config(
                tmpdir,
                '[difflint]\n'
                'max-line-length = 120\n'
                'disable = hard-tab, conflict-marker\n',
            )
            config = load_config(path)
            self.assertEqual(config.max_line_length, 120)
            self.assertEqual(config.disabled_rules, frozenset({'hard-tab', 'conflict-marker'}))

    def test_unknown_rule_id_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_config(tmpdir, '[difflint]\ndisable = not-a-real-rule\n')
            with self.assertRaises(ValueError):
                load_config(path)


class BuildRulesTests(unittest.TestCase):
    def test_default_config_builds_all_rules(self):
        self.assertEqual(len(build_rules(Config())), 5)

    def test_disabled_rules_are_excluded(self):
        config = Config(disabled_rules=frozenset({'hard-tab', 'conflict-marker'}))
        rules = build_rules(config)
        self.assertEqual(len(rules), 3)


if __name__ == '__main__':
    unittest.main()
