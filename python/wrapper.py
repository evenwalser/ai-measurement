#!/usr/bin/env python3
"""
Body Measurement API - Python Wrapper Script

This script processes input images and calculates body measurements
using various calibration methods:
- Reference object calibration
- Height-based calibration
- Spatial (LiDAR) calibration
- Direct calibration (using a pre-calculated calibration factor)
"""

import argparse
import json
import os
import sys
import cv2
import numpy as np
import random
from pathlib import Path

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import spatiallm_bridge for LiDAR processing
try:
    from spatiallm_bridge import process_lidar_data, verify_spatiallm_setup
    SPATIALLM_BRIDGE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: SpatialLM bridge import error: {str(e)}", file=sys.stderr)
    SPATIALLM_BRIDGE_AVAILABLE = False

# Try to import mediapipe for pose detection
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("Warning: MediaPipe not available, will use fallback method for person detection", file=sys.stderr)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Body Measurement API Python Wrapper')
    
    # Input and output files
    parser.add_argument('--input', required=True, help='Path to input image')
    parser.add_argument('--output', required=True, help='Path to output processed image')
    
    # Calibration method
    parser.add_argument('--calibration', required=True, choices=['reference', 'height', 'spatial', 'direct'],
                        help='Calibration method to use')
    
    # Reference object calibration params
    parser.add_argument('--reference_object', help='Reference object type (e.g., a4_paper, credit_card, etc.)')
    parser.add_argument('--reference_width', type=float, help='Reference object width in centimeters')
    parser.add_argument('--reference_height', type=float, help='Reference object height in centimeters')
    
    # Height-based calibration params
    parser.add_argument('--person_height', type=float, help='Person height in centimeters')
    
    # Spatial calibration params
    parser.add_argument('--depth_map', help='Path to depth map data JSON file')
    parser.add_argument('--camera_intrinsics', help='Camera intrinsics JSON string')
    
    # Direct calibration
    parser.add_argument('--calibration_factor', type=float, help='Pre-calculated calibration factor')
    
    return parser.parse_args()

def get_reference_object_dimensions(reference_object):
    """Get standard dimensions for common reference objects."""
    reference_objects = {
        'a4_paper': {'width': 21.0, 'height': 29.7},
        'letter_paper': {'width': 21.59, 'height': 27.94},
        'credit_card': {'width': 8.56, 'height': 5.4},
        'dollar_bill': {'width': 15.6, 'height': 6.6},
        'euro_bill': {'width': 12.0, 'height': 6.2},
        '30cm_ruler': {'width': 30.0, 'height': 3.0},
    }
    
    if reference_object in reference_objects:
        return reference_objects[reference_object]
    else:
        raise ValueError(f"Unknown reference object: {reference_object}")

def detect_person_height_mediapipe(image):
    """Detect person height in the image using MediaPipe."""
    if not MEDIAPIPE_AVAILABLE:
        return None
    
    mp_pose = mp.solutions.pose
    
    # Initialize MediaPipe Pose
    with mp_pose.Pose(static_image_mode=True, model_complexity=2, min_detection_confidence=0.5) as pose:
        # Convert the BGR image to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)

        if not results.pose_landmarks:
            return None

        # Get landmarks
        landmarks = results.pose_landmarks.landmark
        
        # Get the top of the head (approximated by the highest keypoint)
        min_y = float('inf')
        for landmark in landmarks:
            if landmark.visibility > 0.5 and landmark.y < min_y:
                min_y = landmark.y
        
        # Find the feet (ankles are more reliable than feet/heels/toes)
        left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value]
        right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value]
        
        # Use the ankle with higher visibility, or average if both are visible
        foot_y = None
        if left_ankle.visibility > 0.5 and right_ankle.visibility > 0.5:
            foot_y = (left_ankle.y + right_ankle.y) / 2
        elif left_ankle.visibility > 0.5:
            foot_y = left_ankle.y
        elif right_ankle.visibility > 0.5:
            foot_y = right_ankle.y
        else:
            return None
        
        # Calculate height in pixels
        height_px = (foot_y - min_y) * image.shape[0]
        return height_px

def detect_person_height_fallback(image):
    """Fallback method to detect person using simple image processing."""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply threshold to get a binary image
    _, binary = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY_INV)
    
    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None
    
    # Find the largest contour (assuming it's the person)
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Get the bounding rectangle
    x, y, w, h = cv2.boundingRect(largest_contour)
    
    # Return the height in pixels
    return h

def calculate_height_calibration(image, person_height_cm):
    """Calculate calibration factor using the person's height."""
    # Try MediaPipe first, fallback to simpler method if not available
    person_height_px = detect_person_height_mediapipe(image)
    
    if person_height_px is None:
        person_height_px = detect_person_height_fallback(image)
        
    if person_height_px is None:
        raise ValueError("Could not detect person in the image")
    
    # Calculate calibration factor (cm per pixel)
    calibration_factor = person_height_cm / person_height_px
    
    return calibration_factor

def calculate_reference_calibration(image, ref_width_cm, ref_height_cm):
    """Calculate calibration factor using a reference object."""
    # For simplicity in this mock-up, we'll use a random calibration factor
    # In a real implementation, this would detect the reference object and calculate
    # the calibration factor based on its known dimensions
    
    # Mock detection - assuming we detected a reference object of 200x150 pixels
    detected_ref_width_px = 200
    detected_ref_height_px = 150
    
    # Calculate calibration factor (cm per pixel)
    width_calibration = ref_width_cm / detected_ref_width_px
    height_calibration = ref_height_cm / detected_ref_height_px
    
    # Use the average of width and height calibration
    calibration_factor = (width_calibration + height_calibration) / 2
    
    return calibration_factor

def calculate_spatial_calibration(image_path, depth_map_path=None, point_cloud_path=None, camera_intrinsics_path=None):
    """
    Calculate calibration based on spatial data from LiDAR.
    """
    if not SPATIALLM_BRIDGE_AVAILABLE:
        print("SpatialLM bridge not available, using mock implementation", file=sys.stderr)
        # Mock implementation
        return {
            "type": "spatial",
            "method": "spatial",
            "factor": 0.05,  # Mock calibration factor (cm per pixel)
            "confidence": 0.8,
            "unit": "cm/pixel"
        }
    
    try:
        # Load camera intrinsics if provided
        camera_intrinsics = None
        if camera_intrinsics_path:
            with open(camera_intrinsics_path, 'r') as f:
                camera_intrinsics = json.load(f)
        
        # Load depth data if provided
        depth_data = None
        if depth_map_path:
            with open(depth_map_path, 'r') as f:
                depth_data = json.load(f)
        
        # Process the data using the bridge
        calibration_result = process_lidar_data(
            image_path=image_path,
            depth_data=depth_data,
            point_cloud_path=point_cloud_path,
            camera_intrinsics=camera_intrinsics
        )
        
        return {
            "type": "spatial",
            "method": "spatial",
            "factor": calibration_result["calibration_factor"],
            "confidence": calibration_result["confidence"],
            "unit": "cm/pixel"
        }
    
    except Exception as e:
        # Log the error and fall back to mock implementation
        print(f"Error in spatial calibration: {str(e)}", file=sys.stderr)
        return {
            "type": "spatial",
            "method": "spatial",
            "factor": 0.05,  # Mock calibration factor (cm per pixel)
            "confidence": 0.7,
            "unit": "cm/pixel"
        }

def create_height_visualization(image, height_pixels):
    """Create a visualization showing the detected height"""
    visualization = image.copy()
    height, width, _ = visualization.shape
    
    # Draw a line indicating the detected height
    cv2.line(visualization, (width // 4, height // 4), (width // 4, height // 4 + int(height_pixels)), (0, 255, 0), 2)
    
    # Add text showing the measurement
    cv2.putText(visualization, f"Height: {height_pixels:.1f} px", (width // 4 + 10, height // 4 + int(height_pixels // 2)), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    return visualization

def create_reference_visualization(image, ref_object_type, width_px, height_px):
    """Create a visualization showing the reference object detection"""
    visualization = image.copy()
    height, width, _ = visualization.shape
    
    # Center of the reference object (placeholder for real detection)
    center_x, center_y = width // 2, height // 2
    
    # Draw a rectangle representing the detected reference object
    top_left = (center_x - width_px // 2, center_y - height_px // 2)
    bottom_right = (center_x + width_px // 2, center_y + height_px // 2)
    cv2.rectangle(visualization, top_left, bottom_right, (0, 255, 0), 2)
    
    # Add text showing the object type
    cv2.putText(visualization, ref_object_type, (top_left[0], top_left[1] - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    return visualization

def create_spatial_visualization(image, calibration_result):
    """Create a visualization for spatial calibration results"""
    visualization = image.copy()
    height, width, _ = visualization.shape
    
    # Add text showing calibration factor
    factor = calibration_result.get("factor", 0)
    confidence = calibration_result.get("confidence", 0)
    
    cv2.putText(visualization, f"Spatial Calibration", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    
    cv2.putText(visualization, f"Factor: {factor:.4f} cm/px", (20, 80), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    cv2.putText(visualization, f"Confidence: {confidence:.2f}", (20, 120), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    # If we have object detections from SpatialLM, visualize them
    if "objects" in calibration_result:
        for i, obj in enumerate(calibration_result["objects"]):
            # In a real implementation, we would have coordinates to draw boxes
            y_pos = 160 + i * 40
            cv2.putText(visualization, f"{obj['type']}: {obj['width']:.1f}x{obj['height']:.1f} cm", 
                        (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    
    return visualization

def process_image_with_calibration(image_path, calibration):
    """Process the image and return measurements."""
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    # In a real implementation, this would:
    # 1. Detect the person
    # 2. Extract keypoints
    # 3. Calculate measurements
    # 4. Visualize measurements on the output image
    
    # For this mock implementation, we'll generate random measurements
    # and draw basic visualizations
    calibration_factor = calibration.get("factor", 0.1)
    measurements = mock_base_measurements()
    
    # Scale by calibration factor to get real-world units (cm)
    for key in measurements:
        measurements[key] = measurements[key] * calibration_factor
    
    # Create visualization based on calibration method
    if calibration.get("method") == "height":
        # For height-based calibration, visualize the detected height
        # (using placeholder values for now)
        person_height_cm = 175  # This would come from the actual request
        person_height_px = person_height_cm / calibration_factor
        visualized_image = create_height_visualization(image, person_height_px)
    
    elif calibration.get("method") == "reference":
        # For reference object calibration, visualize the detected reference object
        # (using placeholder values for now)
        ref_object_type = "a4_paper"  # This would come from the actual request
        ref_dimensions = get_reference_object_dimensions(ref_object_type)
        width_px = ref_dimensions["width"] / calibration_factor
        height_px = ref_dimensions["height"] / calibration_factor
        visualized_image = create_reference_visualization(image, ref_object_type, int(width_px), int(height_px))
    
    elif calibration.get("method") == "spatial":
        # For spatial calibration, show the detected objects
        visualized_image = create_spatial_visualization(image, calibration)
    
    else:
        # For direct calibration, just use the basic visualization
        visualized_image = image
    
    # Draw basic measurements on the image
    height, width = visualized_image.shape[:2]
    
    # Add a title
    cv2.putText(visualized_image, "Body Measurements", (width // 2 - 150, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    # Add measurements as text
    y_offset = max(height - 230, 150)  # Start from bottom or avoid overlapping with calibration viz
    for key, value in measurements.items():
        y_offset += 40
        text = f"{key.replace('_', ' ').title()}: {value:.1f} cm"
        cv2.putText(visualized_image, text, (width - 250, y_offset), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    return visualized_image, measurements

def mock_base_measurements():
    """Generate mock measurements for demonstration purposes."""
    # In a real implementation, these would be calculated from detected keypoints
    measurements = {
        'chest': random.uniform(85, 115),
        'waist': random.uniform(70, 100),
        'hips': random.uniform(90, 120),
        'inseam': random.uniform(70, 90),
        'shoulder_width': random.uniform(40, 55),
        'sleeve_length': random.uniform(50, 70),
        'neck': random.uniform(30, 45),
    }
    
    return measurements

def main():
    """Main function to process the image and return measurements."""
    args = parse_args()
    
    try:
        # Check if input file exists
        if not os.path.isfile(args.input):
            raise FileNotFoundError(f"Input file not found: {args.input}")
        
        # Ensure output directory exists
        output_dir = os.path.dirname(args.output)
        os.makedirs(output_dir, exist_ok=True)
        
        # Determine calibration method and calculate calibration factor
        calibration_factor = None
        calibration_method = args.calibration
        calibration_result = None
        
        if calibration_method == 'direct' and args.calibration_factor:
            # Direct calibration using provided factor
            calibration_factor = args.calibration_factor
            calibration_result = {
                "method": "direct",
                "factor": calibration_factor,
                "confidence": 1.0,
                "unit": "cm/pixel"
            }
        
        elif calibration_method == 'height' and args.person_height:
            # Height-based calibration
            image = cv2.imread(args.input)
            if image is None:
                raise ValueError(f"Could not load image: {args.input}")
            
            calibration_factor = calculate_height_calibration(image, args.person_height)
            calibration_result = {
                "method": "height",
                "factor": calibration_factor,
                "confidence": 0.9,
                "unit": "cm/pixel"
            }
        
        elif calibration_method == 'reference':
            # Reference object calibration
            if args.reference_object:
                # Get standard dimensions for the reference object
                dimensions = get_reference_object_dimensions(args.reference_object)
                ref_width = dimensions['width']
                ref_height = dimensions['height']
            elif args.reference_width and args.reference_height:
                # Use custom dimensions
                ref_width = args.reference_width
                ref_height = args.reference_height
            else:
                raise ValueError("Reference object calibration requires either reference_object or reference_width and reference_height")
            
            image = cv2.imread(args.input)
            if image is None:
                raise ValueError(f"Could not load image: {args.input}")
                
            calibration_factor = calculate_reference_calibration(image, ref_width, ref_height)
            calibration_result = {
                "method": "reference",
                "factor": calibration_factor,
                "confidence": 0.85,
                "unit": "cm/pixel",
                "reference": {
                    "type": args.reference_object if args.reference_object else "custom",
                    "width": ref_width,
                    "height": ref_height
                }
            }
        
        elif calibration_method == 'spatial':
            # Spatial (LiDAR) calibration
            camera_intrinsics = None
            if args.camera_intrinsics:
                camera_intrinsics = json.loads(args.camera_intrinsics)
                
            calibration_result = calculate_spatial_calibration(
                args.input, 
                depth_map_path=args.depth_map,
                camera_intrinsics_path=args.camera_intrinsics
            )
            calibration_factor = calibration_result.get("factor", 0.1)
        
        else:
            raise ValueError(f"Invalid or incomplete calibration method: {calibration_method}")
        
        # Process the image and get measurements
        visualized_image, measurements = process_image_with_calibration(args.input, calibration_result)
        
        # Save the processed image
        cv2.imwrite(args.output, visualized_image)
        
        # Add calibration info to the output
        result = {
            'success': True,
            'measurements': measurements,
            'calibration': calibration_result
        }
        
        # Return the measurements as JSON
        print(json.dumps(result))
        
    except Exception as e:
        # Return error as JSON
        error_msg = str(e)
        print(json.dumps({
            'success': False,
            'error': error_msg
        }))
        sys.exit(1)

if __name__ == '__main__':
    main()