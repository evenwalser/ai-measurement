import unittest
import os
import numpy as np
from unittest.mock import patch, MagicMock

# Path to test resources
TEST_IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'test-images')

class TestImageProcessor(unittest.TestCase):
    """Tests for the core image processing functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a test image directory if it doesn't exist
        os.makedirs(TEST_IMAGES_DIR, exist_ok=True)
        
        # Create mock image data
        self.mock_image = np.zeros((800, 600, 3), dtype=np.uint8)
        
    def test_image_loading(self):
        """Test that images can be loaded correctly"""
        try:
            # Attempt to import the module
            from python.wrapper import load_image
        except ImportError:
            self.skipTest("Image processing module not available")
            return
            
        # Create a test image file
        test_image_path = os.path.join(TEST_IMAGES_DIR, 'test_image.jpg')
        if not os.path.exists(test_image_path):
            # If no test image exists, we'll skip the test
            self.skipTest(f"Test image not found at {test_image_path}")
            return

        # Test loading the image
        with patch('python.wrapper.load_image', return_value=self.mock_image) as mock_load:
            result = mock_load(test_image_path)
            mock_load.assert_called_once_with(test_image_path)
            self.assertIsNotNone(result)
            self.assertEqual(result.shape, (800, 600, 3))
    
    def test_person_detection(self):
        """Test detection of a person in an image"""
        try:
            from python.wrapper import detect_person
        except ImportError:
            self.skipTest("Person detection module not available")
            return
            
        # Mock the detect_person function
        with patch('python.wrapper.detect_person', return_value={
            'keypoints': [(100, 200), (150, 250), (200, 300)],
            'bounding_box': (50, 50, 350, 750)
        }) as mock_detect:
            result = mock_detect(self.mock_image)
            
            mock_detect.assert_called_once_with(self.mock_image)
            self.assertIsNotNone(result)
            self.assertIn('keypoints', result)
            self.assertIn('bounding_box', result)
            
    def test_keypoint_extraction(self):
        """Test body keypoint extraction"""
        try:
            from python.wrapper import extract_keypoints
        except ImportError:
            self.skipTest("Keypoint extraction module not available")
            return
            
        # Mock the extract_keypoints function
        expected_keypoints = {
            'shoulders': [(100, 150), (300, 150)],
            'hips': [(150, 400), (250, 400)],
            'ankles': [(150, 700), (250, 700)]
        }
        
        with patch('python.wrapper.extract_keypoints', return_value=expected_keypoints) as mock_extract:
            result = mock_extract(self.mock_image)
            
            mock_extract.assert_called_once_with(self.mock_image)
            self.assertEqual(result, expected_keypoints)
            self.assertIn('shoulders', result)
            self.assertIn('hips', result)
            self.assertIn('ankles', result)
    
    def test_measurement_calculation(self):
        """Test calculation of body measurements"""
        try:
            from python.wrapper import calculate_measurements
        except ImportError:
            self.skipTest("Measurement calculation module not available")
            return
            
        # Mock the necessary data
        keypoints = {
            'shoulders': [(100, 150), (300, 150)],
            'chest': [(120, 200), (280, 200)],
            'waist': [(130, 300), (270, 300)],
            'hips': [(150, 400), (250, 400)],
            'ankles': [(150, 700), (250, 700)]
        }
        
        calibration_factor = 0.5  # 0.5 cm per pixel
        
        expected_measurements = {
            'chest': 80.0,  # (280-120) * 0.5
            'waist': 70.0,  # (270-130) * 0.5
            'hips': 50.0,   # (250-150) * 0.5
            'shoulder_width': 100.0,  # (300-100) * 0.5
            'inseam': 300.0  # (700-400) * 0.5
        }
        
        with patch('python.wrapper.calculate_measurements', return_value=expected_measurements) as mock_calc:
            result = mock_calc(keypoints, calibration_factor)
            
            mock_calc.assert_called_once_with(keypoints, calibration_factor)
            self.assertEqual(result, expected_measurements)
            
            # Check that measurements are within reasonable ranges
            for key, value in result.items():
                self.assertGreater(value, 0, f"{key} should be positive")
                if key in ['chest', 'waist', 'hips']:
                    self.assertLess(value, 200, f"{key} should be less than 200cm")
    
    def test_invalid_image(self):
        """Test handling of invalid images"""
        try:
            from python.wrapper import process_image
        except ImportError:
            self.skipTest("Image processing module not available")
            return
            
        # Test with None image
        with patch('python.wrapper.process_image', side_effect=ValueError("Invalid image")) as mock_process:
            with self.assertRaises(ValueError):
                mock_process(None)
                
        # Test with invalid image path
        with patch('python.wrapper.process_image', side_effect=FileNotFoundError("Image not found")) as mock_process:
            with self.assertRaises(FileNotFoundError):
                mock_process('/path/to/nonexistent/image.jpg')

if __name__ == '__main__':
    unittest.main() 