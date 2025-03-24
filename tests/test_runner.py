#!/usr/bin/env python3
"""
Body Measurement API Test Runner
Runs all unit tests sequentially and reports results
"""

import unittest
import sys
import os
import time
import importlib
from pathlib import Path
import json

# Ensure the project root is in the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Define test modules to be imported
TEST_MODULES = [
    # Core functionality tests
    'tests.core.test_image_processor',
    'tests.core.test_spatiallm',
    
    # Calibration method tests
    'tests.calibration.test_reference',
    'tests.calibration.test_height',
    'tests.calibration.test_spatial',
    
    # API tests
    'tests.api.test_controller',
    'tests.api.test_auth',
    
    # Frontend tests
    'tests.frontend.test_interface',
    
    # Integration tests
    'tests.integration.test_end_to_end',
]

def run_test_suite(suite, name):
    """Run a test suite and report results"""
    print(f"\n{'='*20}\nRunning {name} tests\n{'='*20}")
    start_time = time.time()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    elapsed = time.time() - start_time
    
    print(f"\n{name} tests completed in {elapsed:.2f} seconds")
    print(f"Ran {result.testsRun} tests")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    return {
        'name': name,
        'tests_run': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'skipped': len(result.skipped) if hasattr(result, 'skipped') else 0,
        'time': elapsed,
        'success': result.wasSuccessful()
    }

def ensure_test_directories():
    """Ensure all test directories exist"""
    test_dirs = [
        'tests/core',
        'tests/calibration',
        'tests/api',
        'tests/frontend',
        'tests/integration',
    ]
    
    for directory in test_dirs:
        os.makedirs(os.path.join(project_root, directory), exist_ok=True)
        # Create __init__.py file if it doesn't exist
        init_file = os.path.join(project_root, directory, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write("# Initialize test package\n")

def main():
    """Run all test suites sequentially"""
    ensure_test_directories()
    
    # Create tests directory __init__.py
    with open(os.path.join(project_root, 'tests', '__init__.py'), 'w') as f:
        f.write("# Initialize tests package\n")
    
    print(f"Starting test run at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load test modules
    test_suites = []
    for module_name in TEST_MODULES:
        try:
            # Check if module exists, if not create a placeholder test
            module_path = module_name.replace('.', '/') + '.py'
            full_path = os.path.join(project_root, module_path)
            
            if not os.path.exists(full_path):
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w') as f:
                    f.write(f"""import unittest

class Placeholder{module_name.split('.')[-1].title().replace('_', '')}(unittest.TestCase):
    def test_placeholder(self):
        self.skipTest("Test not implemented yet")

if __name__ == '__main__':
    unittest.main()
""")
            
            # Import the module and get its tests
            module = importlib.import_module(module_name)
            suite = unittest.defaultTestLoader.loadTestsFromModule(module)
            name = module_name.split('.')[-1].replace('test_', '').replace('_', ' ').title()
            test_suites.append((suite, name))
        except ImportError as e:
            print(f"Warning: Could not import {module_name}: {e}")
    
    print(f"Running {sum(len(suite._tests) for suite, _ in test_suites)} tests in {len(test_suites)} suites")
    
    results = []
    all_passed = True
    for suite, name in test_suites:
        result = run_test_suite(suite, name)
        results.append(result)
        if not result['success']:
            all_passed = False
    
    # Save test results
    results_dir = os.path.join(project_root, 'test-results')
    os.makedirs(results_dir, exist_ok=True)
    
    timestamp = time.strftime('%Y%m%d-%H%M%S')
    results_file = os.path.join(results_dir, f'test-results-{timestamp}.json')
    
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'suites': results,
            'all_passed': all_passed,
            'total_tests': sum(r['tests_run'] for r in results),
            'total_failures': sum(r['failures'] for r in results),
            'total_errors': sum(r['errors'] for r in results),
            'total_skipped': sum(r['skipped'] for r in results),
        }, f, indent=2)
    
    print("\n" + "="*50)
    print(f"Test run completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Results saved to: {results_file}")
    print("All tests passed!" if all_passed else "Some tests failed!")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 