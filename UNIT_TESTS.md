# Body Measurement API: Unit Tests

This document outlines the unit tests for each component of the Body Measurement API. These tests verify that each part of the system works as expected in isolation.

## Table of Contents

1. [Core Functionality Tests](#core-functionality-tests)
2. [Calibration Method Tests](#calibration-method-tests)
3. [API Controller Tests](#api-controller-tests) 
4. [Frontend Tests](#frontend-tests)
5. [Integration Tests](#integration-tests)
6. [Running the Tests](#running-the-tests)

## Core Functionality Tests

### ImageProcessor Tests

Tests for the core image processing functionality.

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| IP-01 | `test_image_loading` | Tests that images can be loaded correctly | Image loads with correct dimensions |
| IP-02 | `test_person_detection` | Tests detection of a person in an image | Person is correctly detected |
| IP-03 | `test_keypoint_extraction` | Tests body keypoint extraction | All expected keypoints are extracted |
| IP-04 | `test_measurement_calculation` | Tests calculation of body measurements | Measurements within expected ranges |
| IP-05 | `test_invalid_image` | Tests handling of invalid images | Appropriate error is returned |

### SpatialLM Integration Tests

Tests for the SpatialLM bridge functionality.

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| SL-01 | `test_spatiallm_import` | Tests that SpatialLM can be imported | Import succeeds or gracefully fails |
| SL-02 | `test_process_lidar_data` | Tests processing of LiDAR data | Depth map is correctly processed |
| SL-03 | `test_mock_implementation` | Tests mock implementation when SpatialLM is not available | Mock data is correctly generated |
| SL-04 | `test_depth_map_conversion` | Tests conversion of depth data to depth map | Depth map has correct format |
| SL-05 | `test_spatial_calibration` | Tests calibration using spatial data | Calibration factor is correctly calculated |

## Calibration Method Tests

### Reference Object Calibration Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| ROC-01 | `test_reference_object_detection` | Tests detection of reference objects | Reference object correctly detected |
| ROC-02 | `test_calibration_factor_calculation` | Tests calculation of calibration factor | Factor within expected range |
| ROC-03 | `test_custom_reference_dimensions` | Tests calibration with custom dimensions | Calibration factor correctly calculated |
| ROC-04 | `test_multiple_reference_objects` | Tests handling of multiple objects | Correct object selected for calibration |
| ROC-05 | `test_missing_reference_object` | Tests error handling when no reference object is found | Appropriate error returned |

### Height-based Calibration Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| HBC-01 | `test_height_detection` | Tests detection of person's height in pixels | Height correctly measured |
| HBC-02 | `test_height_calibration_factor` | Tests calculation of calibration factor using height | Factor within expected range |
| HBC-03 | `test_height_extremes` | Tests calibration with extreme height values | Boundary values handled correctly |
| HBC-04 | `test_partial_body_visibility` | Tests handling when full body is not visible | Appropriate error or fallback |

### Spatial Calibration Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| SC-01 | `test_lidar_data_processing` | Tests processing of LiDAR data | Data correctly processed |
| SC-02 | `test_spatial_calibration_factor` | Tests calculation of spatial calibration factor | Factor within expected range |
| SC-03 | `test_missing_lidar_data` | Tests handling when LiDAR data is missing | Appropriate error or fallback |
| SC-04 | `test_camera_intrinsics` | Tests use of camera intrinsics for improved calibration | Calibration accuracy improved |

## API Controller Tests

### MeasurementController Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| MC-01 | `test_getMeasurements_validation` | Tests request validation | Invalid requests rejected |
| MC-02 | `test_image_upload` | Tests image upload functionality | Image correctly saved and processed |
| MC-03 | `test_calibration_method_selection` | Tests selection of calibration method | Correct method selected |
| SC-04 | `test_depth_map_processing` | Tests processing of depth map data | Depth data correctly parsed and used |
| MC-05 | `test_error_handling` | Tests error handling in controller | Errors correctly captured and reported |
| MC-06 | `test_response_format` | Tests format of API response | Response matches expected structure |
| MC-07 | `test_timeout_handling` | Tests handling of script timeouts | Appropriate timeout errors returned |

### API Authentication Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| Auth-01 | `test_valid_api_key` | Tests requests with valid API key | Requests authorized |
| Auth-02 | `test_invalid_api_key` | Tests requests with invalid API key | Requests rejected |
| Auth-03 | `test_missing_api_key` | Tests requests without API key | Requests rejected |
| Auth-04 | `test_rate_limiting` | Tests rate limiting functionality | Excessive requests blocked |

## Frontend Tests

### Testing Interface Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| FE-01 | `test_image_upload_ui` | Tests image upload interface | Images can be uploaded |
| FE-02 | `test_calibration_method_selection` | Tests selection of calibration methods | UI updates based on selection |
| FE-03 | `test_lidar_capture` | Tests LiDAR data capture interface | LiDAR data captured on compatible devices |
| FE-04 | `test_form_validation` | Tests validation of form inputs | Invalid inputs prevented |
| FE-05 | `test_results_display` | Tests display of measurement results | Results correctly displayed |
| FE-06 | `test_device_compatibility` | Tests device compatibility detection | Features enabled/disabled appropriately |

## Integration Tests

Tests that verify different components work together correctly.

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| INT-01 | `test_end_to_end_reference` | Tests end-to-end flow with reference object | Correct measurements returned |
| INT-02 | `test_end_to_end_height` | Tests end-to-end flow with height calibration | Correct measurements returned |
| INT-03 | `test_end_to_end_spatial` | Tests end-to-end flow with spatial calibration | Correct measurements returned |
| INT-04 | `test_calibration_fallback` | Tests fallback between calibration methods | Fallback occurs correctly |
| INT-05 | `test_performance` | Tests system performance with various inputs | Response times within acceptable limits |

## Running the Tests

### Test Runner Script

Below is a script to run all tests sequentially:

```python
# test_runner.py
import unittest
import sys
import os
import time

# Import test modules
from tests.core import test_image_processor, test_spatiallm
from tests.calibration import test_reference, test_height, test_spatial
from tests.api import test_controller, test_auth
from tests.frontend import test_interface
from tests.integration import test_integration

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
    
    return result.wasSuccessful()

def main():
    """Run all test suites sequentially"""
    test_suites = [
        (unittest.defaultTestLoader.loadTestsFromModule(test_image_processor), "Image Processor"),
        (unittest.defaultTestLoader.loadTestsFromModule(test_spatiallm), "SpatialLM Integration"),
        (unittest.defaultTestLoader.loadTestsFromModule(test_reference), "Reference Calibration"),
        (unittest.defaultTestLoader.loadTestsFromModule(test_height), "Height Calibration"),
        (unittest.defaultTestLoader.loadTestsFromModule(test_spatial), "Spatial Calibration"),
        (unittest.defaultTestLoader.loadTestsFromModule(test_controller), "API Controller"),
        (unittest.defaultTestLoader.loadTestsFromModule(test_auth), "API Authentication"),
        (unittest.defaultTestLoader.loadTestsFromModule(test_interface), "Frontend Interface"),
        (unittest.defaultTestLoader.loadTestsFromModule(test_integration), "Integration")
    ]
    
    print(f"Starting test run at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Running {sum(len(suite._tests) for suite, _ in test_suites)} tests in {len(test_suites)} suites")
    
    all_passed = True
    for suite, name in test_suites:
        if not run_test_suite(suite, name):
            all_passed = False
    
    print("\n" + "="*50)
    print(f"Test run completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("All tests passed!" if all_passed else "Some tests failed!")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
```

### Example Test Implementation

Here's an example implementation of one test class:

```python
# tests/calibration/test_height.py
import unittest
import numpy as np
from unittest.mock import patch, MagicMock
from python.wrapper import calculate_height_calibration

class TestHeightCalibration(unittest.TestCase):
    def setUp(self):
        # Set up test data
        self.test_image = np.zeros((800, 600, 3), dtype=np.uint8)
        self.person_height_cm = 175
        
    def test_height_detection(self):
        """Test that person's height in pixels is correctly detected"""
        with patch('python.wrapper.detect_person_height', return_value=500) as mock_detect:
            pixel_height = calculate_height_calibration(self.test_image, self.person_height_cm)
            mock_detect.assert_called_once_with(self.test_image)
            self.assertIsNotNone(pixel_height)
    
    def test_height_calibration_factor(self):
        """Test calculation of calibration factor using height"""
        with patch('python.wrapper.detect_person_height', return_value=500) as mock_detect:
            factor = calculate_height_calibration(self.test_image, self.person_height_cm)
            self.assertAlmostEqual(factor, 175/500, places=4)
    
    def test_height_extremes(self):
        """Test calibration with extreme height values"""
        # Test with very short height
        with patch('python.wrapper.detect_person_height', return_value=400):
            factor_short = calculate_height_calibration(self.test_image, 50)
            self.assertAlmostEqual(factor_short, 50/400, places=4)
            
        # Test with very tall height
        with patch('python.wrapper.detect_person_height', return_value=600):
            factor_tall = calculate_height_calibration(self.test_image, 250)
            self.assertAlmostEqual(factor_tall, 250/600, places=4)
    
    def test_partial_body_visibility(self):
        """Test handling when full body is not visible"""
        with patch('python.wrapper.detect_person_height', return_value=None):
            with self.assertRaises(ValueError):
                calculate_height_calibration(self.test_image, self.person_height_cm)

if __name__ == '__main__':
    unittest.main()
```

### Running Tests

To run all tests:

```bash
python test_runner.py
```

To run a specific test suite:

```bash
python -m unittest tests.core.test_image_processor
```

To run a specific test:

```bash
python -m unittest tests.calibration.test_height.TestHeightCalibration.test_height_detection
``` 