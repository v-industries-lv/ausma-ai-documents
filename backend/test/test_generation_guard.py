import unittest
from generation_guard import GenerationGuard
from settings import GENERATION_GUARD
import itertools

class RerankerTest(unittest.TestCase):
    def test_from_settings(self):
        settings = {
            "generation_guard": {
                "safe_token_threshold": 4000,
                "token_check_interval": 100,
                "max_repeats": 5,
                "window_size": 50
            }
        }

        self.assertIsNotNone(GenerationGuard.from_settings(settings[GENERATION_GUARD]))

    def test_infinite_loop(self):
        settings = {
            "generation_guard": {
                "safe_token_threshold": 0,
                "token_check_interval": 5,
                "max_repeats": 5,
                "window_size": 5
            }
        }
        generation_guard = GenerationGuard.from_settings(settings[GENERATION_GUARD])
        ok_tokens = ['Lorem', 'ipsum', 'dolor', 'sit', 'amet,', 'consectetur', 'adipiscing', 'elit.', 'Nullam', 'dapibus', 'non', 'nisi', 'vitae', 'mollis.']
        generation_guard.check_token_buffer = ok_tokens
        infinite_pattern =["this", "is", "infinite", "pattern,", "window_size", "+1"]
        max_iteration = 500
        num_chunks = len(ok_tokens)
        for iteration, new_token in enumerate(itertools.cycle(infinite_pattern)):
            generation_guard.accumulate_tokens(new_token)
            num_chunks += 1
            if generation_guard.is_infinite_generation():
                print(repr(generation_guard.message_infinite_loop()))
                self.assertTrue(True)
                break
            if iteration >= max_iteration:
                self.assertTrue(False)
                break


if __name__ == '__main__':
    unittest.main()
