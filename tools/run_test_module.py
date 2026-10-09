"""Run unittest classes and plain test functions without silently omitting either."""
import importlib
import faulthandler
import inspect
import os
import sys
import unittest

def suite_for(module):
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    for name, function in inspect.getmembers(module, inspect.isfunction):
        if name.startswith('test_') and function.__module__ == module.__name__:
            suite.addTest(unittest.FunctionTestCase(function))
    return suite

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Provide exactly one test module')
    # Capture a stack just before the parent's bound, including native Qt waits.
    # The parent still owns timeout/process-tree cleanup; this never waives it.
    timeout = int(os.environ.get('MASTIXA_TEST_TIMEOUT', '0'))
    if timeout >= 10:
        faulthandler.dump_traceback_later(timeout - 5)
    module = importlib.import_module(sys.argv[1])
    suite = suite_for(module)
    if not suite.countTestCases():
        raise SystemExit('No test cases found; refusing a silent pass')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    faulthandler.cancel_dump_traceback_later()
    raise SystemExit(not result.wasSuccessful())
