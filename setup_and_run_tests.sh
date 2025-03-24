#!/bin/bash
# Body Measurement API Test Setup and Runner
# This script sets up the test environment and runs all tests

# Enable error handling
set -e

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Print banner
echo -e "${GREEN}"
echo "=============================================="
echo "  Body Measurement API Test Suite"
echo "=============================================="
echo -e "${NC}"

# Create necessary directory structure
echo -e "${YELLOW}Setting up test environment...${NC}"

# Create test directories
mkdir -p tests/core
mkdir -p tests/calibration
mkdir -p tests/api
mkdir -p tests/frontend
mkdir -p tests/integration
mkdir -p test-images
mkdir -p test-results

# Create __init__.py files to make directories importable
touch tests/__init__.py
touch tests/core/__init__.py
touch tests/calibration/__init__.py
touch tests/api/__init__.py
touch tests/frontend/__init__.py
touch tests/integration/__init__.py

# Create placeholder test image if one doesn't exist
if [ ! -f "test-images/test_person.jpg" ]; then
    echo -e "${YELLOW}Creating placeholder test image...${NC}"
    # Try to use the convert command (ImageMagick) if available
    if command -v convert &> /dev/null; then
        convert -size 800x600 xc:black -fill white -draw "rectangle 250,200 350,700" \
            -draw "circle 300,150 300,100" \
            -draw "rectangle 150,300 250,600" \
            -draw "rectangle 350,300 450,600" \
            test-images/test_person.jpg
    else
        # Fallback to creating an empty file
        touch test-images/test_person.jpg
        echo -e "${RED}Warning: ImageMagick not found. Created empty test image.${NC}"
    fi
fi

# Create a mock-up wrapper.py if it doesn't exist
if [ ! -f "python/wrapper.py" ]; then
    echo -e "${YELLOW}Creating placeholder wrapper.py...${NC}"
    mkdir -p python
    mkdir -p python/spatiallm
    
    cat > python/wrapper.py << 'EOL'
#!/usr/bin/env python3
"""
Body Measurement API Wrapper
This is a placeholder script for testing
"""

import argparse
import json
import os
import sys
import random

def load_image(image_path):
    """Mock function to load an image"""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    return "mock_image_data"

def detect_person(image):
    """Mock function to detect a person in an image"""
    return {
        'keypoints': [(100, 200), (150, 250), (200, 300)],
        'bounding_box': (50, 50, 350, 750)
    }

def detect_person_height(image):
    """Mock function to detect person's height in pixels"""
    return 500

def extract_keypoints(image):
    """Mock function to extract body keypoints"""
    return {
        'shoulders': [(100, 150), (300, 150)],
        'chest': [(120, 200), (280, 200)],
        'waist': [(130, 300), (270, 300)],
        'hips': [(150, 400), (250, 400)],
        'ankles': [(150, 700), (250, 700)]
    }

def calculate_measurements(keypoints, calibration_factor):
    """Mock function to calculate body measurements"""
    return {
        'chest': 98.5,
        'waist': 84.2,
        'hips': 102.1,
        'inseam': 78.3,
        'shoulder_width': 45.6,
        'sleeve_length': 64.8,
        'neck': 37.9
    }

def calculate_height_calibration(image, person_height_cm):
    """Mock function to calculate calibration factor using height"""
    pixel_height = detect_person_height(image)
    if pixel_height is None:
        raise ValueError("Full body not visible in image")
    return person_height_cm / pixel_height

def process_image(image_path, calibration_method, **kwargs):
    """Mock function to process an image and return measurements"""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    # Mock calibration based on method
    calibration = {
        'factor': 0.2,
        'confidence': 0.9,
        'unit': 'cm/pixel'
    }
    
    if calibration_method == 'reference':
        calibration['method'] = 'reference'
        if 'reference_object' in kwargs:
            calibration['reference_object'] = kwargs['reference_object']
    elif calibration_method == 'height':
        calibration['method'] = 'height'
        if 'person_height' in kwargs:
            calibration['person_height'] = kwargs['person_height']
    elif calibration_method == 'spatial':
        calibration['method'] = 'spatial'
        if 'depth_data' in kwargs and os.path.exists(kwargs['depth_data']):
            calibration['confidence'] = 0.98
        else:
            # Fallback to height if provided
            if 'person_height' in kwargs:
                calibration['method'] = 'height'
                calibration['person_height'] = kwargs['person_height']
                calibration['fallback_reason'] = "Spatial calibration failed: No LiDAR data available"
    elif calibration_method == 'direct':
        calibration['method'] = 'direct'
        if 'calibration_factor' in kwargs:
            calibration['factor'] = float(kwargs['calibration_factor'])
    
    # Generate mock measurements
    measurements = calculate_measurements(None, calibration['factor'])
    
    # Add some random variation to make each run slightly different
    for key in measurements:
        measurements[key] = round(measurements[key] + random.uniform(-1.0, 1.0), 1)
    
    return {
        'success': True,
        'measurements': measurements,
        'calibration': calibration
    }

def main():
    """Parse arguments and process image"""
    parser = argparse.ArgumentParser(description="Body Measurement API")
    parser.add_argument("--input", required=True, help="Path to input image")
    parser.add_argument("--output", help="Path to output JSON file")
    parser.add_argument("--calibration_method", choices=['reference', 'height', 'spatial', 'direct'], 
                        default='reference', help="Calibration method")
    parser.add_argument("--reference_object", choices=['a4_paper', 'letter_paper', 'credit_card', 
                                                    'dollar_bill', 'euro_bill', '30cm_ruler'],
                        help="Type of reference object in the image")
    parser.add_argument("--reference_width", type=float, 
                        help="Width of custom reference object in cm")
    parser.add_argument("--reference_height", type=float, 
                        help="Height of custom reference object in cm")
    parser.add_argument("--person_height", type=float, 
                        help="Person's height in cm")
    parser.add_argument("--calibration_factor", type=float, 
                        help="Pre-calculated calibration factor (cm/pixel)")
    parser.add_argument("--depth_data", help="Path to depth data JSON file")
    
    args = parser.parse_args()
    
    # Process the image
    try:
        result = process_image(
            args.input,
            args.calibration_method,
            reference_object=args.reference_object,
            reference_width=args.reference_width,
            reference_height=args.reference_height,
            person_height=args.person_height,
            calibration_factor=args.calibration_factor,
            depth_data=args.depth_data
        )
        
        # Output the result
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
        
        # Always print to stdout for piping
        print(json.dumps(result))
        return 0
    
    except Exception as e:
        error_result = {
            'success': False,
            'message': "Error processing image",
            'error': str(e)
        }
        
        # Output the error
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(error_result, f, indent=2)
        
        # Always print to stdout for piping
        print(json.dumps(error_result))
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOL

    # Make it executable
    chmod +x python/wrapper.py
fi

# Create a placeholder spatiallm_bridge.py if it doesn't exist
if [ ! -f "python/spatiallm/bridge.py" ]; then
    echo -e "${YELLOW}Creating placeholder spatiallm_bridge.py...${NC}"
    mkdir -p python/spatiallm
    
    cat > python/spatiallm/bridge.py << 'EOL'
#!/usr/bin/env python3
"""
SpatialLM Bridge Module
This is a placeholder script for testing
"""

import json
import os
import random
import numpy as np

def is_spatiallm_available():
    """Check if the SpatialLM library is available"""
    try:
        # This will always fail in this mock implementation
        import nonexistent_spatiallm
        return True
    except ImportError:
        return False

def process_lidar_data(depth_data_path, image_path):
    """Process LiDAR data to get spatial information"""
    if not os.path.exists(depth_data_path):
        raise FileNotFoundError(f"Depth data not found: {depth_data_path}")
    
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    # Check if we can use the real implementation
    if is_spatiallm_available():
        return real_spatiallm_processing(depth_data_path, image_path)
    else:
        return mock_spatiallm_processing(depth_data_path, image_path)

def real_spatiallm_processing(depth_data_path, image_path):
    """Process using the real SpatialLM library (not implemented in mock)"""
    raise NotImplementedError("Real SpatialLM processing not available")

def convert_depth_data_to_depth_map(depth_data_path):
    """Convert depth data JSON to depth map array"""
    with open(depth_data_path, 'r') as f:
        data = json.load(f)
    
    width = data.get('width', 256)
    height = data.get('height', 192)
    depth_values = data.get('data', [0.0] * (width * height))
    
    # Convert to numpy array and reshape
    depth_map = np.array(depth_values, dtype=np.float32).reshape(height, width)
    return depth_map

def mock_spatiallm_processing(depth_data_path, image_path):
    """Mock implementation for testing"""
    # Load the depth data
    try:
        depth_map = convert_depth_data_to_depth_map(depth_data_path)
    except Exception as e:
        raise ValueError(f"Error processing depth data: {str(e)}")
    
    # Generate a mock calibration factor
    # In a real implementation, this would be calculated from the depth data
    calibration_factor = 0.23 + random.uniform(-0.02, 0.02)
    
    return {
        'calibration_factor': calibration_factor,
        'confidence': 0.98,
        'average_depth': float(np.mean(depth_map)),
        'unit': 'cm/pixel'
    }

def calculate_spatial_calibration(image_path, depth_data_path):
    """Calculate calibration factor using LiDAR spatial data"""
    try:
        result = process_lidar_data(depth_data_path, image_path)
        return result['calibration_factor']
    except Exception as e:
        raise ValueError(f"Spatial calibration failed: {str(e)}")
EOL
fi

# Make script executable
chmod +x setup_and_run_tests.sh

# Create a mock controller if needed
if [ ! -d "api/app/Http/Controllers" ]; then
    echo -e "${YELLOW}Creating placeholder MeasurementController.php...${NC}"
    mkdir -p api/app/Http/Controllers
    
    cat > api/app/Http/Controllers/MeasurementController.php << 'EOL'
<?php
// This is a placeholder for testing

namespace App\Http\Controllers;

class MeasurementController extends Controller
{
    public function getMeasurements($request)
    {
        // This is just a placeholder
        return [
            'success' => true,
            'message' => 'This is a placeholder controller'
        ];
    }
}
EOL
fi

echo -e "${GREEN}Test environment setup complete!${NC}"

# Run the tests
echo -e "${YELLOW}Running test suite...${NC}"
python3 tests/test_runner.py

echo -e "${GREEN}All done!${NC}" 