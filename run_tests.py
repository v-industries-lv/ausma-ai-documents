import unittest
import os
import sys
import platform

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = os.path.join(ROOT_DIR, "test")

# Ensure "test" is on import path
sys.path.insert(0, ROOT_DIR)
os_dict = {
    'Linux': "linux",
    'Darwin': "macos",
    'Windows': "windows",
}
os_type = os_dict.get(platform.system())
if os_type is None:
    sys.exit(f"System not recognized. Got: {os_type}, expected {os_dict.keys()}")
os.environ["XPDF_PATH"] = os.path.join(os.getcwd(), "bin", os_type, "pdftopng")

os.chdir(TEST_DIR)

loader = unittest.TestLoader()
suite = loader.discover(start_dir=TEST_DIR)

runner = unittest.TextTestRunner(verbosity=2)
runner.run(suite)