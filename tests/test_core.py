import unittest

from aiden_core import AidenEngine


class CoreSanityTests(unittest.TestCase):
    def test_parse_max_messages_defaults_for_invalid_value(self):
        self.assertEqual(AidenEngine._parse_max_messages('abc'), 30)

    def test_parse_max_messages_enforces_minimum(self):
        self.assertEqual(AidenEngine._parse_max_messages('1'), 5)

    def test_parse_max_messages_accepts_valid_int(self):
        self.assertEqual(AidenEngine._parse_max_messages('40'), 40)

    def test_sanitize_profile_normalizes_invalid_fields(self):
        payload = {
            'name': '   ',
            'mode': 'unknown-mode',
            'short_responses': 'maybe',
            'tasks': 'bad',
            'memory_notes': {'bad': 'value'},
        }
        result = AidenEngine._sanitize_profile(payload)
        self.assertEqual(result['name'], 'User')
        self.assertEqual(result['mode'], 'study')
        self.assertEqual(result['short_responses'], 'false')
        self.assertEqual(result['tasks'], [])
        self.assertEqual(result['memory_notes'], [])


if __name__ == '__main__':
    unittest.main()
