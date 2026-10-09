"""Run unittest classes and plain test functions without silently omitting either."""
import importlib
import inspect
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
    module = importlib.import_module(sys.argv[1])
    suite = suite_for(module)
    if not suite.countTestCases():
        raise SystemExit('No test cases found; refusing a silent pass')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
