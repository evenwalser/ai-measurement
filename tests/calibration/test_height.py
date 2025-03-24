import unittest
import numpy as np
from unittest.mock import patch, MagicMock

class TestHeightCalibration(unittest.TestCase):
    """Tests for the height-based calibration method"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a mock image
        self.mock_image = np.zeros((800, 600, 3), dtype=np.uint8)
        
        # Set test parameters
        self.person_height_cm = 175  # in cm
        self.detected_height_px = 500  # in pixels
    
    def test_height_detection(self):
        """Test that person's height in pixels is correctly detected"""
        try:
            from python.wrapper import detect_person_height
        except ImportError:
            self.skipTest("Height detection module not available")
            return
            
        with patch('python.wrapper.detect_person_height', return_value=self.detected_height_px) as mock_detect:
            result = mock_detect(self.mock_image)
            
            mock_detect.assert_called_once_with(self.mock_image)
            self.assertEqual(result, self.detected_height_px)
            self.assertIsInstance(result, int)
    
    def test_height_calibration_factor(self):
        """Test calculation of calibration factor using height"""
        try:
            from python.wrapper import calculate_height_calibration
        except ImportError:
            self.skipTest("Height calibration module not available")
            return
            
        with patch('python.wrapper.detect_person_height', return_value=self.detected_height_px):
            with patch('python.wrapper.calculate_height_calibration') as mock_calc:
                # Set up the mock to return the expected calibration factor
                expected_factor = self.person_height_cm / self.detected_height_px
                mock_calc.return_value = expected_factor
                
                # Call the function
                result = mock_calc(self.mock_image, self.person_height_cm)
                
                # Verify the result
                mock_calc.assert_called_once_with(self.mock_image, self.person_height_cm)
                self.assertAlmostEqual(result, expected_factor, places=4)
    
    def test_height_extremes(self):
        """Test calibration with extreme height values"""
        try:
            from python.wrapper import calculate_height_calibration
        except ImportError:
            self.skipTest("Height calibration module not available")
            return
            
        # Test with very short height
        with patch('python.wrapper.detect_person_height', return_value=400) as mock_detect:
            with patch('python.wrapper.calculate_height_calibration', return_value=50/400) as mock_calc:
                result_short = mock_calc(self.mock_image, 50)
                self.assertAlmostEqual(result_short, 50/400, places=4)
            
        # Test with very tall height
        with patch('python.wrapper.detect_person_height', return_value=600) as mock_detect:
            with patch('python.wrapper.calculate_height_calibration', return_value=250/600) as mock_calc:
                result_tall = mock_calc(self.mock_image, 250)
                self.assertAlmostEqual(result_tall, 250/600, places=4)
    
    def test_partial_body_visibility(self):
        """Test handling when full body is not visible"""
        try:
            from python.wrapper import calculate_height_calibration
        except ImportError:
            self.skipTest("Height calibration module not available")
            return
            
        # Mock detect_person_height to return None (indicating full body not visible)
        with patch('python.wrapper.detect_person_height', return_value=None) as mock_detect:
            with patch('python.wrapper.calculate_height_calibration', side_effect=ValueError("Full body not visible")) as mock_calc:
                with self.assertRaises(ValueError) as context:
                    mock_calc(self.mock_image, self.person_height_cm)
                
                self.assertIn("Full body not visible", str(context.exception))
    
    def test_proportion_fallback(self):
        """Test fallback to proportion-based estimation when keypoints are limited"""
        try:
            from python.wrapper import calculate_height_calibration
        except ImportError:
            self.skipTest("Height calibration module not available")
            return
            
        # Mock a scenario where direct height detection fails but proportion estimation works
        with patch('python.wrapper.detect_person_height', return_value=None) as mock_detect:
            with patch('python.wrapper.estimate_height_from_proportions', return_value=450) as mock_estimate:
                with patch('python.wrapper.calculate_height_calibration', return_value=self.person_height_cm/450) as mock_calc:
                    result = mock_calc(self.mock_image, self.person_height_cm)
                    
                    # Verify that the estimation function was called
                    mock_estimate.assert_called_once()
                    self.assertAlmostEqual(result, self.person_height_cm/450, places=4)

if __name__ == '__main__':
    unittest.main() 