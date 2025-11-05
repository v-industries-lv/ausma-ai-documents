import os
import unittest

from settings import Settings
from settings import LLM_RUNNERS, DEFAULT_SYSTEM_PROMPT, SUPPORTED_LLM_RUNNERS, KBSTORES, DOC_SOURCES

# test file
def tf(name: str) -> str:
    return os.sep.join(['settings', name])


class SettingTestCase(unittest.TestCase):
    def test_empty(self):
        self.assertEqual({}, Settings(tf("DOES_NOT_EXIST.conf"), tf("DOES_NOT_EXIST.conf")).get_all())
        self.assertEqual({}, Settings(tf("DOES_NOT_EXIST.conf"), tf("empty.conf")).get_all())
        self.assertEqual({}, Settings(tf("empty.conf"), tf("DOES_NOT_EXIST.conf")).get_all())
        self.assertEqual({}, Settings(tf("empty.conf"), tf("empty.conf")).get_all())
        self.assertEqual({}, Settings(tf("blank.conf"), tf("blank.conf")).get_all())
        self.assertEqual({}, Settings(tf("empty.conf"), tf("blank.conf")).get_all())
        self.assertEqual({}, Settings(tf("blank.conf"), tf("empty.conf")).get_all())

    def test_override(self):
        self.assertEqual({'a': 'AAA'}, Settings(tf("a.conf"), tf("a.conf")).get_all())
        self.assertEqual({'a': 'AAA'}, Settings(tf("empty.conf"), tf("a.conf")).get_all())
        self.assertEqual({'a': 'AAA'}, Settings(tf("a.conf"), tf("empty.conf")).get_all())
        self.assertEqual({'a': '2AAA'}, Settings(tf("a.conf"), tf("a2.conf")).get_all())
        self.assertEqual({'a': 'AAA'}, Settings(tf("a2.conf"), tf("a.conf")).get_all())
        self.assertEqual({'a': 'AAA','b':'BBBB'}, Settings(tf("a.conf"), tf("b.conf")).get_all())
        self.assertEqual({'a': 'AAA','b':'2BBBB'}, Settings(tf("a.conf"), tf("b2.conf")).get_all())
        self.assertEqual({'a': 'AAA','b':'2BBBB'}, Settings(tf("b2.conf"), tf("a.conf")).get_all())

    def test_llm_runner_validation(self):
        settings = Settings(tf("mock_default.conf"), tf("mock_current.conf"))

        test_val = ""
        with self.assertRaises(Exception) as cm:
            settings[LLM_RUNNERS] = ""
        self.assertEqual(str(cm.exception), f"Errors:\n{["LLM runner config must be a dict type, got <class 'str'> instead."]}")
        self.assertNotEqual(settings[LLM_RUNNERS], test_val)

        test_val = {}
        with self.assertRaises(Exception) as cm:
            settings[LLM_RUNNERS] = test_val
        self.assertEqual(str(cm.exception), f"Errors:\n{['LLM runner config key "type" not found', 'LLM runner config key "name" not found']}")
        self.assertNotEqual(settings[LLM_RUNNERS], test_val)

        test_val = {"type": "not supported"}
        with self.assertRaises(Exception) as cm:
            settings[LLM_RUNNERS] = test_val
        self.assertEqual(str(cm.exception), f"Errors:\n{[f"LLM runner type not supported not in supported list: ['{"', '".join(SUPPORTED_LLM_RUNNERS)}']", 'LLM runner config key "name" not found']}")
        self.assertNotEqual(settings[LLM_RUNNERS], test_val)

        test_val = {"type": "debug"}
        with self.assertRaises(Exception) as cm:
            settings[LLM_RUNNERS] = test_val
        self.assertEqual(str(cm.exception), f"Errors:\n{['LLM runner config key "name" not found']}")
        self.assertNotEqual(settings[LLM_RUNNERS], test_val)

        test_val = {"type": "debug", "name": None}
        with self.assertRaises(Exception) as cm:
            settings[LLM_RUNNERS] = test_val
        self.assertEqual(str(cm.exception), f"Errors:\n{["LLM runner name must by 'str' type! Got: <class 'NoneType'>"]}")
        self.assertNotEqual(settings[LLM_RUNNERS], test_val)

        test_val = {"type": "debug", "name": ""}
        with self.assertRaises(Exception) as cm:
            settings[LLM_RUNNERS] = test_val
        self.assertEqual(str(cm.exception), f"Errors:\n{['LLM runner name cannot be empty!']}")
        self.assertNotEqual(settings[LLM_RUNNERS], test_val)

        test_val = [{"type": "debug", "host": "localhost"}]
        with self.assertRaises(Exception) as cm:
            settings[LLM_RUNNERS] = test_val
        self.assertEqual(str(cm.exception), f"Errors:\n{['LLM runner config key "name" not found']}")
        self.assertNotEqual(settings[LLM_RUNNERS], test_val)

        test_val = [{"type": "debug", "name": "valid_name", "host": ":123456"}]
        with self.assertRaises(Exception) as cm:
            settings[LLM_RUNNERS] = test_val
        self.assertEqual(str(cm.exception), f"Errors:\n{['LLM runner host :123456 is invalid.']}")
        self.assertNotEqual(settings[LLM_RUNNERS], test_val)

    def test_default_system_prompt_validation(self):
        settings = Settings(tf("mock_default.conf"), tf("mock_current.conf"))
        with self.assertRaises(Exception) as cm:
            settings[DEFAULT_SYSTEM_PROMPT] = None
        self.assertEqual(str(cm.exception), f"Errors:\n{["Key default_system_prompt value must be a str type, got <class 'NoneType'> instead."]}")

    def test_unknown_setting_key_validation(self):
        settings = Settings(tf("mock_default.conf"), tf("mock_current.conf"))
        settings["unknown_setting"] = None
        self.assertIsNone(settings["unknown_setting"])

    def test_get_llm_runners(self):
        settings = Settings(tf("mock_default.conf"), tf("mock_current.conf"))
        runners = settings.get_llm_runners()
        self.assertEqual(runners, settings[LLM_RUNNERS])

    def test_get_llm_runners_modify_return(self):
        settings = Settings(tf("mock_default.conf"), tf("mock_current.conf"))
        runners = settings.get_llm_runners()
        runners.pop()
        self.assertNotEqual(runners, settings[LLM_RUNNERS])
        runners = settings.get_llm_runners()
        runners[0] = {}
        self.assertNotEqual(runners, settings[LLM_RUNNERS])

    def test_get_kbstores(self):
        settings = Settings(tf("mock_default.conf"), tf("mock_current.conf"))
        runners = settings.get_kbstores()
        self.assertEqual(runners, settings[KBSTORES])

    def test_get_kbstores_modify_return(self):
        settings = Settings(tf("mock_default.conf"), tf("mock_current.conf"))
        runners = settings.get_kbstores()
        runners.pop()
        self.assertNotEqual(runners, settings[KBSTORES])
        runners = settings.get_kbstores()
        runners[0] = {}
        self.assertNotEqual(runners, settings[KBSTORES])

    def test_get_doc_sources(self):
        settings = Settings(tf("mock_default.conf"), tf("mock_current.conf"))
        runners = settings.get_doc_sources()
        self.assertEqual(runners, settings[DOC_SOURCES])

    def test_get_doc_sources_modify_return(self):
        settings = Settings(tf("mock_default.conf"), tf("mock_current.conf"))
        runners = settings.get_doc_sources()
        runners.pop()
        self.assertNotEqual(runners, settings[DOC_SOURCES])
        runners = settings.get_doc_sources()
        runners[0] = {}
        self.assertNotEqual(runners, settings[DOC_SOURCES])


if __name__ == '__main__':
    unittest.main()
