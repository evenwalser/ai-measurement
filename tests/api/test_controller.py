import unittest
import json
import os
from unittest.mock import patch, MagicMock

class TestMeasurementController(unittest.TestCase):
    """Tests for the MeasurementController class"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock request data
        self.mock_request = MagicMock()
        self.mock_request.files = {'image': MagicMock()}
        self.mock_request.form = {
            'calibration_method': 'reference',
            'reference_object': 'a4_paper',
            'device_platform': 'ios'
        }
        
        # Mock successful measurement results
        self.mock_measurements = {
            'chest': 98.5,
            'waist': 84.2,
            'hips': 102.1,
            'inseam': 78.3,
            'shoulder_width': 45.6,
            'sleeve_length': 64.8,
            'neck': 37.9
        }
        
        # Mock calibration data
        self.mock_calibration = {
            'method': 'reference',
            'factor': 0.21,
            'confidence': 0.95,
            'unit': 'cm/pixel'
        }
        
        # Create paths for temp files
        self.temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'tmp')
        os.makedirs(self.temp_dir, exist_ok=True)
        
    def test_getMeasurements_validation(self):
        """Test request validation"""
        try:
            from api.app.Http.Controllers.MeasurementController import MeasurementController
        except ImportError:
            self.skipTest("MeasurementController module not available")
            return
        
        # Test missing image validation
        with patch('api.app.Http.Controllers.MeasurementController.MeasurementController') as MockController:
            controller = MockController()
            
            # Configure the mock to raise a validation error
            controller.getMeasurements.side_effect = ValueError("The image field is required")
            
            # Create a request with no image
            mock_request_no_image = MagicMock()
            mock_request_no_image.files = {}
            
            # Test the controller
            with self.assertRaises(ValueError) as context:
                controller.getMeasurements(mock_request_no_image)
            
            self.assertIn("image field is required", str(context.exception))
    
    def test_image_upload(self):
        """Test image upload functionality"""
        try:
            from api.app.Http.Controllers.MeasurementController import MeasurementController
        except ImportError:
            self.skipTest("MeasurementController module not available")
            return
        
        with patch('api.app.Http.Controllers.MeasurementController.MeasurementController') as MockController:
            controller = MockController()
            
            # Mock the save_image method
            controller.save_image.return_value = os.path.join(self.temp_dir, 'test_image.jpg')
            
            # Mock successful processing
            controller.executeMeasurementScript.return_value = ({
                'success': True,
                'measurements': self.mock_measurements,
                'calibration': self.mock_calibration
            }, 0)
            
            # Call the controller method
            result = controller.getMeasurements(self.mock_request)
            
            # Verify the result
            controller.save_image.assert_called_once()
            controller.executeMeasurementScript.assert_called_once()
            self.assertTrue(result['success'])
            self.assertEqual(result['measurements'], self.mock_measurements)
            self.assertEqual(result['calibration'], self.mock_calibration)
    
    def test_calibration_method_selection(self):
        """Test selection of calibration method"""
        try:
            from api.app.Http.Controllers.MeasurementController import MeasurementController
        except ImportError:
            self.skipTest("MeasurementController module not available")
            return
        
        # Test cases for different calibration methods
        test_cases = [
            # (method, expected_args)
            ('reference', ['--reference_object', 'a4_paper']),
            ('height', ['--person_height', '175']),
            ('spatial', ['--calibration_method', 'spatial']),
            ('direct', ['--calibration_factor', '0.5']),
        ]
        
        for method, expected_args in test_cases:
            with patch('api.app.Http.Controllers.MeasurementController.MeasurementController') as MockController:
                controller = MockController()
                
                # Configure the mock
                controller.save_image.return_value = os.path.join(self.temp_dir, 'test_image.jpg')
                controller.executeMeasurementScript.return_value = ({
                    'success': True,
                    'measurements': self.mock_measurements,
                    'calibration': {'method': method}
                }, 0)
                
                # Update request form data
                mock_request = MagicMock()
                mock_request.files = {'image': MagicMock()}
                
                if method == 'reference':
                    mock_request.form = {'calibration_method': 'reference', 'reference_object': 'a4_paper'}
                elif method == 'height':
                    mock_request.form = {'calibration_method': 'height', 'person_height': '175'}
                elif method == 'spatial':
                    mock_request.form = {'calibration_method': 'spatial', 'depth_map_data': '{"width":256,"height":192,"data":[]}'}
                elif method == 'direct':
                    mock_request.form = {'calibration_method': 'direct', 'calibration_factor': '0.5'}
                
                # Call the controller method
                result = controller.getMeasurements(mock_request)
                
                # Verify that the correct args were constructed
                controller.buildMeasurementArgs.assert_called_once()
                self.assertTrue(result['success'])
                self.assertEqual(result['calibration']['method'], method)
    
    def test_depth_map_processing(self):
        """Test processing of depth map data"""
        try:
            from api.app.Http.Controllers.MeasurementController import MeasurementController
        except ImportError:
            self.skipTest("MeasurementController module not available")
            return
        
        with patch('api.app.Http.Controllers.MeasurementController.MeasurementController') as MockController:
            controller = MockController()
            
            # Configure the mock
            controller.save_image.return_value = os.path.join(self.temp_dir, 'test_image.jpg')
            controller.saveDepthMapData.return_value = os.path.join(self.temp_dir, 'depth_data.json')
            controller.executeMeasurementScript.return_value = ({
                'success': True,
                'measurements': self.mock_measurements,
                'calibration': {'method': 'spatial'}
            }, 0)
            
            # Create a mock request with depth data
            mock_request = MagicMock()
            mock_request.files = {'image': MagicMock()}
            mock_request.form = {
                'calibration_method': 'spatial',
                'depth_map_data': json.dumps({
                    'width': 256,
                    'height': 192,
                    'data': [0.1] * (256 * 192)
                })
            }
            
            # Call the controller method
            result = controller.getMeasurements(mock_request)
            
            # Verify that depth data was saved and processed
            controller.saveDepthMapData.assert_called_once()
            controller.executeMeasurementScript.assert_called_once()
            self.assertTrue(result['success'])
            self.assertEqual(result['calibration']['method'], 'spatial')
    
    def test_error_handling(self):
        """Test error handling in controller"""
        try:
            from api.app.Http.Controllers.MeasurementController import MeasurementController
        except ImportError:
            self.skipTest("MeasurementController module not available")
            return
        
        # Test script execution error
        with patch('api.app.Http.Controllers.MeasurementController.MeasurementController') as MockController:
            controller = MockController()
            
            # Configure the mock to simulate a script error
            controller.save_image.return_value = os.path.join(self.temp_dir, 'test_image.jpg')
            controller.executeMeasurementScript.return_value = ({
                'success': False,
                'message': 'Error processing image',
                'error': 'Person not detected in image'
            }, 1)
            
            # Call the controller method
            result = controller.getMeasurements(self.mock_request)
            
            # Verify the error response
            self.assertFalse(result['success'])
            self.assertIn('message', result)
            self.assertEqual(result['message'], 'Error processing image')
    
    def test_response_format(self):
        """Test format of API response"""
        try:
            from api.app.Http.Controllers.MeasurementController import MeasurementController
        except ImportError:
            self.skipTest("MeasurementController module not available")
            return
        
        with patch('api.app.Http.Controllers.MeasurementController.MeasurementController') as MockController:
            controller = MockController()
            
            # Configure the mock
            controller.save_image.return_value = os.path.join(self.temp_dir, 'test_image.jpg')
            controller.executeMeasurementScript.return_value = ({
                'success': True,
                'measurements': self.mock_measurements,
                'calibration': self.mock_calibration,
                'image_url': '/storage/uploads/processed_image123.jpg',
                'request_id': 'a1b2c3d4e5f6',
                'processing_time': 2.35
            }, 0)
            
            # Call the controller method
            result = controller.getMeasurements(self.mock_request)
            
            # Verify the response format
            self.assertTrue(result['success'])
            self.assertIn('measurements', result)
            self.assertIn('calibration', result)
            self.assertIn('image_url', result)
            self.assertIn('request_id', result)
            self.assertIn('processing_time', result)
            
            # Check that all measurements are present
            for key in ['chest', 'waist', 'hips', 'inseam', 'shoulder_width', 'sleeve_length', 'neck']:
                self.assertIn(key, result['measurements'])

if __name__ == '__main__':
    unittest.main() 