#!/usr/bin/env python3
"""
Generate Test Data for Body Measurement API

This script generates sample test data for the Body Measurement API,
including mock depth data for testing spatial calibration.
"""

import os
import json
import random
import numpy as np
from pathlib import Path

# Ensure output directories exist
def ensure_dirs():
    """Create necessary output directories if they don't exist."""
    os.makedirs('test-data/depth-maps', exist_ok=True)
    os.makedirs('test-data/results', exist_ok=True)
    print("Created output directories")

def generate_depth_map(width=320, height=240, filename='test-depth-map.json'):
    """
    Generate a mock depth map for testing spatial calibration.
    
    Args:
        width: Width of the depth map in pixels
        height: Height of the depth map in pixels
        filename: Output filename
    
    Returns:
        Path to the generated file
    """
    # Create a mock depth map with a gradient and a "person" shape
    depth_map = np.zeros((height, width), dtype=np.float32)
    
    # Set background gradient (farther away)
    for y in range(height):
        for x in range(width):
            depth_map[y, x] = 3.0 + 0.01 * (x + y) / (width + height)
    
    # Create a "person" silhouette (closer)
    center_x = width // 2
    center_y = height // 2
    person_width = width // 3
    person_height = height * 3 // 4
    
    for y in range(center_y - person_height // 2, center_y + person_height // 2):
        if y < 0 or y >= height:
            continue
            
        for x in range(center_x - person_width // 2, center_x + person_width // 2):
            if x < 0 or x >= width:
                continue
                
            # Calculate distance to center of the person shape
            dx = (x - center_x) / (person_width // 2)
            dy = (y - (center_y - person_height // 4)) / (person_height // 2)
            distance = np.sqrt(dx**2 + dy**2)
            
            if distance <= 1.0:
                # Person is closer to the camera (smaller depth values)
                # Shape the depth with a smooth curve
                depth = 1.5 + 0.5 * distance
                depth_map[y, x] = depth
    
    # Convert to flat array for JSON serialization
    depth_data = {
        'width': width,
        'height': height,
        'data': depth_map.flatten().tolist(),
        'intrinsics': [
            [width, 0, width/2],
            [0, height, height/2],
            [0, 0, 1]
        ],
        'timestamp': 0
    }
    
    # Save to file
    output_path = os.path.join('test-data/depth-maps', filename)
    with open(output_path, 'w') as f:
        json.dump(depth_data, f)
    
    print(f"Generated depth map: {output_path}")
    return output_path

def generate_mock_measurements(num_samples=5):
    """
    Generate mock measurement results for testing.
    
    Args:
        num_samples: Number of sample results to generate
    """
    calibration_methods = ['reference', 'height', 'spatial']
    reference_objects = ['a4_paper', 'credit_card', 'letter_paper', 'dollar_bill']
    
    for i in range(num_samples):
        method = random.choice(calibration_methods)
        calibration_factor = random.uniform(0.05, 0.2)
        
        # Generate random measurements
        measurements = {
            'chest': random.uniform(85, 115),
            'waist': random.uniform(70, 100),
            'hips': random.uniform(90, 120),
            'inseam': random.uniform(70, 90),
            'shoulder_width': random.uniform(40, 55),
            'sleeve_length': random.uniform(50, 70),
            'neck': random.uniform(30, 45),
        }
        
        # Apply calibration factor
        measurements = {k: v * calibration_factor for k, v in measurements.items()}
        
        # Create calibration info based on method
        calibration = {
            'method': method,
            'factor': calibration_factor
        }
        
        if method == 'reference':
            calibration['reference_object'] = random.choice(reference_objects)
        elif method == 'height':
            calibration['person_height'] = random.uniform(150, 200)
        
        # Create result object
        result = {
            'success': True,
            'measurements': measurements,
            'calibration': calibration,
            'image_url': f'/storage/uploads/sample_{i+1}.jpg'
        }
        
        # Save to file
        output_path = os.path.join('test-data/results', f'sample_result_{i+1}.json')
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"Generated mock result: {output_path}")

def main():
    """Main function to generate test data."""
    print("Generating test data for Body Measurement API...")
    
    # Create directories
    ensure_dirs()
    
    # Generate depth maps
    for i in range(3):
        generate_depth_map(
            width=320, 
            height=240, 
            filename=f'depth_map_{i+1}.json'
        )
    
    # Generate mock measurement results
    generate_mock_measurements(num_samples=5)
    
    print("Test data generation complete.")

if __name__ == "__main__":
    main() 