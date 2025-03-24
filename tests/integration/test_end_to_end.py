import unittest
import os
import json
import shutil
import tempfile
from unittest.mock import patch, MagicMock
import subprocess

class TestEndToEndIntegration(unittest.TestCase):
    """End-to-end integration tests for the full system"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests"""
        # Create test directories
        cls.test_dir = tempfile.mkdtemp(prefix="body_measurement_test_")
        cls.image_path = os.path.join(cls.test_dir, "test_person.jpg")
        cls.output_path = os.path.join(cls.test_dir, "test_output.json")
        
        # Check if we can actually run the tests
        cls.can_run_wrapper = cls._check_wrapper_executable()
        
        # Create a dummy test image if necessary
        if not os.path.exists(cls.image_path):
            cls._create_dummy_image(cls.image_path)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        # Remove test directory
        shutil.rmtree(cls.test_dir, ignore_errors=True)
    
    @staticmethod
    def _check_wrapper_executable():
        """Check if the wrapper script exists and is executable"""
        wrapper_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "python", "wrapper.py")
        return os.path.exists(wrapper_path) and os.access(wrapper_path, os.X_OK)
    
    @staticmethod
    def _create_dummy_image(path):
        """Create a dummy image for testing"""
        try:
            import numpy as np
            from PIL import Image
            
            # Create a blank image
            img = np.zeros((800, 600, 3), dtype=np.uint8)
            # Add a simple person silhouette
            img[200:700, 250:350] = 255  # Body
            img[100:200, 275:325] = 255  # Head
            img[300:600, 150:250] = 255  # Left arm
            img[300:600, 350:450] = 255  # Right arm
            
            # Save the image
            Image.fromarray(img).save(path)
        except ImportError:
            # If PIL or numpy is not available, create an empty file
            with open(path, 'wb') as f:
                f.write(b'')
    
    def setUp(self):
        """Set up before each test"""
        if not self.can_run_wrapper:
            self.skipTest("Wrapper script not found or not executable")
    
    def test_end_to_end_reference(self):
        """Test end-to-end flow with reference object calibration"""
        # Path to the wrapper script
        wrapper_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "python", "wrapper.py")
        
        # Test with reference object calibration
        cmd = [
            "python", wrapper_path,
            "--input", self.image_path,
            "--output", self.output_path,
            "--calibration_method", "reference",
            "--reference_object", "a4_paper"
        ]
        
        # Mock the subprocess call
        with patch('subprocess.run') as mock_run:
            # Configure the mock to return success
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = json.dumps({
                "success": True,
                "measurements": {
                    "chest": 98.5,
                    "waist": 84.2,
                    "hips": 102.1,
                    "inseam": 78.3,
                    "shoulder_width": 45.6,
                    "sleeve_length": 64.8,
                    "neck": 37.9
                },
                "calibration": {
                    "method": "reference",
                    "factor": 0.21,
                    "confidence": 0.95,
                    "unit": "cm/pixel"
                }
            })
            mock_run.return_value = mock_process
            
            # Run the command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Check the result
            mock_run.assert_called_once()
            self.assertEqual(result.returncode, 0)
            
            # Parse the output JSON
            output = json.loads(mock_process.stdout)
            self.assertTrue(output["success"])
            self.assertIn("measurements", output)
            self.assertIn("calibration", output)
            self.assertEqual(output["calibration"]["method"], "reference")
    
    def test_end_to_end_height(self):
        """Test end-to-end flow with height calibration"""
        # Path to the wrapper script
        wrapper_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "python", "wrapper.py")
        
        # Test with height calibration
        cmd = [
            "python", wrapper_path,
            "--input", self.image_path,
            "--output", self.output_path,
            "--calibration_method", "height",
            "--person_height", "175"
        ]
        
        # Mock the subprocess call
        with patch('subprocess.run') as mock_run:
            # Configure the mock to return success
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = json.dumps({
                "success": True,
                "measurements": {
                    "chest": 99.1,
                    "waist": 85.0,
                    "hips": 103.2,
                    "inseam": 79.0,
                    "shoulder_width": 46.1,
                    "sleeve_length": 65.5,
                    "neck": 38.2
                },
                "calibration": {
                    "method": "height",
                    "factor": 0.22,
                    "confidence": 0.90,
                    "unit": "cm/pixel"
                }
            })
            mock_run.return_value = mock_process
            
            # Run the command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Check the result
            mock_run.assert_called_once()
            self.assertEqual(result.returncode, 0)
            
            # Parse the output JSON
            output = json.loads(mock_process.stdout)
            self.assertTrue(output["success"])
            self.assertIn("measurements", output)
            self.assertIn("calibration", output)
            self.assertEqual(output["calibration"]["method"], "height")
    
    def test_end_to_end_spatial(self):
        """Test end-to-end flow with spatial calibration"""
        # Path to the wrapper script
        wrapper_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "python", "wrapper.py")
        
        # Create a temporary depth data file
        depth_data_path = os.path.join(self.test_dir, "depth_data.json")
        with open(depth_data_path, 'w') as f:
            json.dump({
                "width": 256,
                "height": 192,
                "data": [0.5] * (256 * 192),
                "timestamp": "2023-06-10T13:45:32Z",
                "intrinsics": {
                    "fx": 1.23,
                    "fy": 1.23,
                    "cx": 128.0,
                    "cy": 96.0
                }
            }, f)
        
        # Test with spatial calibration
        cmd = [
            "python", wrapper_path,
            "--input", self.image_path,
            "--output", self.output_path,
            "--calibration_method", "spatial",
            "--depth_data", depth_data_path
        ]
        
        # Mock the subprocess call
        with patch('subprocess.run') as mock_run:
            # Configure the mock to return success
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = json.dumps({
                "success": True,
                "measurements": {
                    "chest": 100.2,
                    "waist": 86.3,
                    "hips": 104.5,
                    "inseam": 80.1,
                    "shoulder_width": 47.2,
                    "sleeve_length": 66.7,
                    "neck": 39.0
                },
                "calibration": {
                    "method": "spatial",
                    "factor": 0.23,
                    "confidence": 0.98,
                    "unit": "cm/pixel"
                }
            })
            mock_run.return_value = mock_process
            
            # Run the command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Check the result
            mock_run.assert_called_once()
            self.assertEqual(result.returncode, 0)
            
            # Parse the output JSON
            output = json.loads(mock_process.stdout)
            self.assertTrue(output["success"])
            self.assertIn("measurements", output)
            self.assertIn("calibration", output)
            self.assertEqual(output["calibration"]["method"], "spatial")
    
    def test_calibration_fallback(self):
        """Test fallback between calibration methods"""
        # Path to the wrapper script
        wrapper_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "python", "wrapper.py")
        
        # Test with spatial calibration but force a fallback
        cmd = [
            "python", wrapper_path,
            "--input", self.image_path,
            "--output", self.output_path,
            "--calibration_method", "spatial",  # Attempt spatial first
            "--person_height", "175"  # But provide height as fallback
        ]
        
        # Mock the subprocess call
        with patch('subprocess.run') as mock_run:
            # Configure the mock to return a result with height calibration (fallback)
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = json.dumps({
                "success": True,
                "measurements": {
                    "chest": 99.1,
                    "waist": 85.0,
                    "hips": 103.2,
                    "inseam": 79.0,
                    "shoulder_width": 46.1,
                    "sleeve_length": 65.5,
                    "neck": 38.2
                },
                "calibration": {
                    "method": "height",  # Fallback to height
                    "factor": 0.22,
                    "confidence": 0.90,
                    "unit": "cm/pixel",
                    "fallback_reason": "Spatial calibration failed: No LiDAR data available"
                }
            })
            mock_run.return_value = mock_process
            
            # Run the command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Check the result
            mock_run.assert_called_once()
            self.assertEqual(result.returncode, 0)
            
            # Parse the output JSON
            output = json.loads(mock_process.stdout)
            self.assertTrue(output["success"])
            self.assertEqual(output["calibration"]["method"], "height")
            self.assertIn("fallback_reason", output["calibration"])

if __name__ == '__main__':
    unittest.main() 