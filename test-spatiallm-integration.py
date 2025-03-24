#!/usr/bin/env python3
"""
Test Script for SpatialLM Integration

This script demonstrates the integration of SpatialLM with the Body Measurement API
by testing the functionality of the spatiallm_bridge.py module.
"""

import os
import sys
import json
import argparse
import numpy as np
import cv2
from pathlib import Path

# Add python directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "python"))

# Import our bridge module
try:
    from spatiallm_bridge import (
        process_lidar_data,
        verify_spatiallm_setup,
        convert_depth_data_to_depth_map,
        create_point_cloud_from_depth,
        SPATIALLM_AVAILABLE,
        SPATIALLM_IMPORT_SOURCE
    )
except ImportError as e:
    print(f"Error importing spatiallm_bridge: {e}")
    sys.exit(1)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Test SpatialLM Integration')
    parser.add_argument('--image', help='Path to input image', default='test-images/sample.jpg')
    parser.add_argument('--depth', help='Path to depth data JSON file', default=None)
    parser.add_argument('--point_cloud', help='Path to point cloud PLY file', default=None)
    parser.add_argument('--generate_mock', action='store_true', help='Generate mock depth data if no depth data provided')
    
    return parser.parse_args()

def check_spatiallm_setup():
    """Check if SpatialLM is properly set up."""
    print("\n=== SpatialLM Setup Check ===")
    print(f"SpatialLM Available: {SPATIALLM_AVAILABLE}")
    if SPATIALLM_AVAILABLE:
        print(f"SpatialLM Import Source: {SPATIALLM_IMPORT_SOURCE}")
        
        # Try to verify the setup
        if verify_spatiallm_setup():
            print("SpatialLM Setup Verification: PASSED")
        else:
            print("SpatialLM Setup Verification: FAILED")
    else:
        print("SpatialLM is not available. Will use mock implementation.")

def generate_mock_depth_data(image_path):
    """Generate mock depth data for the given image."""
    print("\n=== Generating Mock Depth Data ===")
    
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image {image_path}")
        return None
    
    height, width = image.shape[:2]
    
    # Create a simple depth map (grayscale image as depth)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Normalize and invert (closer objects are brighter)
    depth = 1.0 - (gray.astype(np.float32) / 255.0)
    
    # Scale to reasonable depth values (0.5m to 5m)
    depth = 0.5 + depth * 4.5
    
    # Create depth data JSON
    depth_data = {
        "width": width,
        "height": height,
        "data": depth.flatten().tolist(),
        "timestamp": 0
    }
    
    # Save to a temporary file
    output_path = f"{os.path.splitext(image_path)[0]}_mock_depth.json"
    with open(output_path, 'w') as f:
        json.dump(depth_data, f)
    
    print(f"Mock depth data saved to: {output_path}")
    return output_path

def process_data(image_path, depth_path=None, point_cloud_path=None):
    """Process the image and depth data using the spatiallm_bridge module."""
    print("\n=== Processing Data ===")
    print(f"Image: {image_path}")
    print(f"Depth Data: {depth_path}")
    print(f"Point Cloud: {point_cloud_path}")
    
    # Load depth data if provided
    depth_data = None
    if depth_path:
        try:
            with open(depth_path, 'r') as f:
                depth_data = json.load(f)
            print("Depth data loaded successfully")
        except Exception as e:
            print(f"Error loading depth data: {e}")
            return
    
    # Process the data
    try:
        result = process_lidar_data(
            image_path=image_path,
            depth_data=depth_data,
            point_cloud_path=point_cloud_path
        )
        
        print("\n=== Calibration Result ===")
        for key, value in result.items():
            if key == "reference_objects" or key == "objects" or key == "walls":
                print(f"{key}: {len(value)} items")
                for i, obj in enumerate(value[:3]):  # Print first 3 objects
                    print(f"  {i+1}. {obj}")
                if len(value) > 3:
                    print(f"  ... and {len(value) - 3} more")
            else:
                print(f"{key}: {value}")
        
        return result
        
    except Exception as e:
        print(f"Error processing data: {e}")
        return None

def create_visualization(image_path, result):
    """Create a visualization of the calibration result."""
    print("\n=== Creating Visualization ===")
    
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image {image_path}")
        return
    
    # Create a copy for visualization
    visualization = image.copy()
    height, width = visualization.shape[:2]
    
    # Add calibration factor
    factor = result.get("calibration_factor", 0)
    confidence = result.get("confidence", 0)
    
    cv2.putText(visualization, f"SpatialLM Calibration Test", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    
    cv2.putText(visualization, f"Calibration Factor: {factor:.4f} cm/px", (20, 80), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    cv2.putText(visualization, f"Confidence: {confidence:.2f}", (20, 120), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    # If we have object detections, visualize them
    y_pos = 160
    
    # Reference objects
    if "reference_objects" in result:
        for i, obj in enumerate(result["reference_objects"]):
            y_pos += 40
            cv2.putText(visualization, f"Ref {i+1}: {obj.get('type', 'unknown')} - "
                        f"{obj.get('width_cm', 0):.1f}x{obj.get('height_cm', 0):.1f} cm", 
                        (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    
    # Regular objects
    if "objects" in result:
        for i, obj in enumerate(result["objects"]):
            y_pos += 40
            cv2.putText(visualization, f"Obj {i+1}: {obj.get('type', 'unknown')} - "
                        f"{obj.get('width', 0):.1f}x{obj.get('height', 0):.1f} cm", 
                        (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # Save the visualization
    output_path = f"{os.path.splitext(image_path)[0]}_spatiallm_viz.jpg"
    cv2.imwrite(output_path, visualization)
    print(f"Visualization saved to: {output_path}")

def main():
    """Main function."""
    args = parse_args()
    
    # Check if the image exists
    if not os.path.isfile(args.image):
        print(f"Error: Input image not found: {args.image}")
        return
    
    # Check SpatialLM setup
    check_spatiallm_setup()
    
    # Generate mock depth data if requested
    if args.generate_mock and not args.depth and not args.point_cloud:
        args.depth = generate_mock_depth_data(args.image)
    
    # Process the data
    result = process_data(args.image, args.depth, args.point_cloud)
    
    # Create visualization if processing was successful
    if result:
        create_visualization(args.image, result)

if __name__ == "__main__":
    main() 