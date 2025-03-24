#!/usr/bin/env python3
"""
Body Measurement API Wrapper

This script acts as a bridge between the API and the measurement algorithm.
It processes an image using the underlying AI model to extract body measurements.
Supports multiple calibration methods including spatial calibration from LiDAR.
"""

import argparse
import json
import os
import sys
import traceback
import cv2
import numpy as np
import tempfile
from pathlib import Path

# Optional imports for SpatialLM integration
try:
    import torch
    SPATIAL_LM_AVAILABLE = True
except ImportError:
    SPATIAL_LM_AVAILABLE = False

def main():
    """
    Main function to process an image and extract body measurements.
    """
    parser = argparse.ArgumentParser(description='Extract body measurements from an image.')
    parser.add_argument('--input', required=True, help='Path to the input image')
    
    # Calibration method selection
    parser.add_argument('--calibration_method', choices=['reference', 'height', 'spatial', 'direct'], 
                        help='Calibration method to use')
    
    # Reference object parameters
    parser.add_argument('--reference_object', choices=['a4_paper', 'credit_card', 'letter', 'custom'], 
                        help='Standard reference object type')
    parser.add_argument('--ref_width', type=float, help='Width of reference object in cm')
    parser.add_argument('--ref_height', type=float, help='Height of reference object in cm')
    
    # Height-based calibration parameters
    parser.add_argument('--person_height', type=float, help='Person\'s height in cm for calibration')
    
    # Direct calibration parameter
    parser.add_argument('--calibration_factor', type=float, help='Pre-calculated calibration factor')
    
    # Spatial calibration parameters
    parser.add_argument('--depth_map', help='Path to depth map from LiDAR (JSON or binary format)')
    parser.add_argument('--point_cloud', help='Path to point cloud for spatial calibration')
    parser.add_argument('--camera_intrinsics', help='Camera intrinsics for spatial calibration')
    
    parser.add_argument('--output', help='Output path for processed image')
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not os.path.isfile(args.input):
        print(json.dumps({
            "error": f"Input file does not exist: {args.input}"
        }))
        return 1
    
    try:
        # Determine calibration method and parameters
        calibration_method = args.calibration_method if args.calibration_method else determine_calibration_method(args)
        calibration = None
        
        if calibration_method == 'direct' and args.calibration_factor:
            # Direct calibration factor
            calibration = {
                "type": "direct",
                "method": "direct",
                "factor": args.calibration_factor,
                "unit": "cm/pixel"
            }
        
        elif calibration_method == 'height' and args.person_height:
            # Height-based calibration
            calibration = calculate_height_based_calibration(args.input, args.person_height)
        
        elif calibration_method == 'spatial':
            # Spatial calibration using LiDAR
            if not SPATIAL_LM_AVAILABLE:
                print(json.dumps({
                    "error": "Spatial calibration requires PyTorch and SpatialLM dependencies"
                }))
                return 1
                
            if args.depth_map or args.point_cloud:
                calibration = calculate_spatial_calibration(
                    args.input, 
                    depth_map_path=args.depth_map, 
                    point_cloud_path=args.point_cloud,
                    camera_intrinsics_path=args.camera_intrinsics
                )
            else:
                print(json.dumps({
                    "error": "Spatial calibration requires depth map or point cloud data"
                }))
                return 1
        
        elif calibration_method == 'reference':
            # Reference object calibration
            if args.reference_object == 'custom':
                if not args.ref_width or not args.ref_height:
                    print(json.dumps({
                        "error": "Custom reference object requires width and height parameters"
                    }))
                    return 1
                ref_width = args.ref_width
                ref_height = args.ref_height
            else:
                # Use standard reference object dimensions
                if args.reference_object == 'a4_paper':
                    ref_width = 21.0  # cm
                    ref_height = 29.7  # cm
                elif args.reference_object == 'letter':
                    ref_width = 21.59  # cm
                    ref_height = 27.94  # cm
                elif args.reference_object == 'credit_card':
                    ref_width = 8.56  # cm
                    ref_height = 5.398  # cm
                else:
                    print(json.dumps({
                        "error": f"Unknown reference object type: {args.reference_object}"
                    }))
                    return 1
            
            calibration = calculate_reference_object_calibration(
                args.input, args.reference_object, ref_width, ref_height)
        
        else:
            print(json.dumps({
                "error": "No valid calibration method provided. Please provide one of: reference object, person's height, calibration factor, or LiDAR data."
            }))
            return 1
        
        if not calibration:
            print(json.dumps({
                "error": "Calibration failed. Please check your inputs."
            }))
            return 1
        
        # Process the image to extract measurements
        measurements = process_image_with_calibration(args.input, calibration)
        
        # Return measurements as JSON
        print(json.dumps({
            "measurements": measurements,
            "calibration": calibration
        }))
        
        # Save output image if requested
        if args.output and "visualization" in calibration:
            cv2.imwrite(args.output, calibration["visualization"])
        
        return 0
        
    except Exception as e:
        # Print the error as JSON
        print(json.dumps({
            "error": str(e),
            "traceback": traceback.format_exc()
        }))
        return 1

def determine_calibration_method(args):
    """
    Determine the best calibration method based on provided arguments.
    """
    if args.calibration_factor:
        return 'direct'
    elif args.person_height:
        return 'height'
    elif args.depth_map or args.point_cloud:
        return 'spatial'
    elif args.reference_object or (args.ref_width and args.ref_height):
        return 'reference'
    else:
        # Default to reference object with a4 paper
        return 'reference'

def calculate_height_based_calibration(image_path, person_height_cm):
    """
    Calculate calibration based on person's height.
    """
    try:
        person_height_pixels = detect_person_height(image_path)
        
        if not person_height_pixels:
            raise ValueError("Could not detect full person in image. Please ensure the entire body is visible.")
                
        # Calculate calibration factor (cm per pixel)
        calibration_factor = person_height_cm / person_height_pixels
        
        # Create visualization
        image = cv2.imread(image_path)
        visualization = create_height_visualization(image, person_height_pixels)
        
        return {
            "type": "height_based",
            "method": "height",
            "factor": calibration_factor,
            "person_height_cm": person_height_cm,
            "person_height_pixels": person_height_pixels,
            "unit": "cm/pixel",
            "visualization": visualization
        }
    except Exception as e:
        raise ValueError(f"Height-based calibration failed: {str(e)}")

def create_height_visualization(image, height_pixels):
    """
    Create a visualization of the detected person height.
    """
    # Clone the image to avoid modifying the original
    visualization = image.copy()
    
    # Draw a line representing the detected height
    h, w = image.shape[:2]
    center_x = w // 2
    top_y = h // 2 - height_pixels // 2
    bottom_y = h // 2 + height_pixels // 2
    
    # Draw the height line
    cv2.line(visualization, (center_x, top_y), (center_x, bottom_y), (0, 255, 0), 2)
    
    # Draw markers at top and bottom
    cv2.circle(visualization, (center_x, top_y), 5, (0, 0, 255), -1)
    cv2.circle(visualization, (center_x, bottom_y), 5, (0, 0, 255), -1)
    
    # Add text
    cv2.putText(visualization, f"Height: {height_pixels:.1f} px", 
                (center_x + 10, (top_y + bottom_y) // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    return visualization

def calculate_reference_object_calibration(image_path, ref_object_type, ref_width_cm, ref_height_cm):
    """
    Calculate calibration based on reference object.
    This is a mock implementation - in a real system, you would detect the reference object.
    """
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not load image from {image_path}")
    
    # In a real implementation, you would detect the reference object and its dimensions
    # For this mock implementation, we'll simulate detection with some randomization
    h, w = image.shape[:2]
    
    # Simulate detection of reference object (in a real system, this would use object detection)
    ref_obj_width_px = w * 0.3  # Simulate detected width in pixels
    ref_obj_height_px = ref_obj_width_px * (ref_height_cm / ref_width_cm)  # Maintain aspect ratio
    
    # Calculate calibration factor (cm per pixel)
    width_factor = ref_width_cm / ref_obj_width_px
    height_factor = ref_height_cm / ref_obj_height_px
    
    # Average the factors for more robustness
    calibration_factor = (width_factor + height_factor) / 2
    
    # Create a visualization
    visualization = create_reference_visualization(image, ref_object_type, ref_obj_width_px, ref_obj_height_px)
    
    return {
        "type": "reference_object",
        "method": "reference",
        "reference": ref_object_type,
        "width_cm": ref_width_cm,
        "height_cm": ref_height_cm,
        "width_px": ref_obj_width_px,
        "height_px": ref_obj_height_px,
        "factor": calibration_factor,
        "unit": "cm/pixel",
        "visualization": visualization
    }

def create_reference_visualization(image, ref_object_type, width_px, height_px):
    """
    Create a visualization of the detected reference object.
    """
    # Clone the image to avoid modifying the original
    visualization = image.copy()
    
    # Calculate center position for the reference object
    h, w = image.shape[:2]
    center_x = w // 2
    center_y = h // 2
    
    # Calculate corners of the reference object
    left = int(center_x - width_px / 2)
    top = int(center_y - height_px / 2)
    right = int(center_x + width_px / 2)
    bottom = int(center_y + height_px / 2)
    
    # Draw rectangle for the reference object
    cv2.rectangle(visualization, (left, top), (right, bottom), (0, 255, 0), 2)
    
    # Add label
    cv2.putText(visualization, f"Reference: {ref_object_type}", 
                (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    return visualization

def calculate_spatial_calibration(image_path, depth_map_path=None, point_cloud_path=None, camera_intrinsics_path=None):
    """
    Calculate calibration based on spatial data from LiDAR.
    This requires SpatialLM integration.
    """
    if not SPATIAL_LM_AVAILABLE:
        raise ImportError("Spatial calibration requires PyTorch and SpatialLM")
    
    try:
        # Import SpatialLM (in a real implementation, this would be properly structured)
        sys.path.append(os.path.join(os.path.dirname(__file__), "spatiallm"))
        from spatiallm_bridge import process_lidar_data
        
        # Process the spatial data
        if depth_map_path:
            # Load and process depth map
            with open(depth_map_path, 'r') as f:
                depth_data = json.load(f)
            
            calibration_result = process_lidar_data(image_path, depth_data=depth_data)
        elif point_cloud_path:
            # Process point cloud
            calibration_result = process_lidar_data(image_path, point_cloud_path=point_cloud_path)
        else:
            raise ValueError("Either depth map or point cloud data must be provided")
        
        # Load image for visualization
        image = cv2.imread(image_path)
        visualization = create_spatial_visualization(image, calibration_result)
        
        return {
            "type": "spatial",
            "method": "spatial",
            "factor": calibration_result["calibration_factor"],
            "confidence": calibration_result["confidence"],
            "unit": "cm/pixel",
            "visualization": visualization
        }
    
    except ImportError:
        # Fallback if SpatialLM isn't available - mock the response for development
        print("Warning: SpatialLM not available, using mock spatial calibration", file=sys.stderr)
        
        # Mock calibration result with reasonable values
        image = cv2.imread(image_path)
        mock_factor = 0.08  # 1 pixel = 0.08 cm (example)
        
        visualization = image.copy()
        h, w = image.shape[:2]
        cv2.putText(visualization, "MOCK SPATIAL CALIBRATION", 
                    (w//2 - 150, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        return {
            "type": "spatial",
            "method": "spatial",
            "factor": mock_factor,
            "confidence": 0.95,
            "unit": "cm/pixel",
            "is_mock": True,
            "visualization": visualization
        }

def create_spatial_visualization(image, calibration_result):
    """
    Create a visualization of the spatial calibration.
    """
    # Clone the image to avoid modifying the original
    visualization = image.copy()
    
    # Draw calibration information
    h, w = image.shape[:2]
    text = f"Spatial Calibration: {calibration_result['calibration_factor']:.4f} cm/px"
    cv2.putText(visualization, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # Draw confidence
    conf_text = f"Confidence: {calibration_result['confidence']:.2f}"
    cv2.putText(visualization, conf_text, (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Draw grid representing spatial understanding
    grid_size = 50
    for x in range(0, w, grid_size):
        cv2.line(visualization, (x, 0), (x, h), (0, 255, 0), 1)
    for y in range(0, h, grid_size):
        cv2.line(visualization, (0, y), (w, y), (0, 255, 0), 1)
    
    return visualization

def detect_person_height(image_path):
    """
    Detect a person in the image and calculate their height in pixels.
    Uses MediaPipe Pose detection or fallback to basic contour detection.
    """
    try:
        # Try to import mediapipe for advanced pose detection
        import mediapipe as mp
        from mediapipe.python.solutions import pose as mp_pose
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image from {image_path}")
        
        # Initialize pose detection
        with mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            enable_segmentation=True,
            min_detection_confidence=0.5) as pose:
            
            # Convert image to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Process image
            results = pose.process(image_rgb)
            
            if not results.pose_landmarks:
                # Fallback to basic contour method if no landmarks detected
                return detect_person_height_basic(image_path)
                
            # Get relevant landmarks for height calculation
            landmarks = results.pose_landmarks.landmark
            
            # Check if we have full body visibility
            if (landmarks[mp_pose.PoseLandmark.NOSE].visibility > 0.5 and 
                landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE].visibility > 0.5 and
                landmarks[mp_pose.PoseLandmark.LEFT_ANKLE].visibility > 0.5):
                
                # Calculate top (head) point
                top_y = landmarks[mp_pose.PoseLandmark.NOSE].y * image.shape[0]
                
                # Calculate bottom (feet) point - average of both ankles
                left_ankle_y = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE].y * image.shape[0]
                right_ankle_y = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE].y * image.shape[0]
                bottom_y = (left_ankle_y + right_ankle_y) / 2
                
                # Calculate height in pixels
                height_pixels = bottom_y - top_y
                
                return abs(height_pixels)
            else:
                # If body parts aren't fully visible, try basic method
                return detect_person_height_basic(image_path)
    
    except (ImportError, Exception) as e:
        # Fallback to basic contour method if MediaPipe fails
        print(f"MediaPipe detection failed: {str(e)}, falling back to basic method", file=sys.stderr)
        return detect_person_height_basic(image_path)

def detect_person_height_basic(image_path):
    """
    Fallback method to estimate person height using basic image processing.
    Less accurate than MediaPipe but doesn't require additional libraries.
    """
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not load image from {image_path}")
    
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Threshold the image
    _, thresh = cv2.threshold(blurred, 20, 255, cv2.THRESH_BINARY)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None
    
    # Find the largest contour (assuming it's the person)
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Get bounding rectangle
    x, y, w, h = cv2.boundingRect(largest_contour)
    
    # The height of the bounding rectangle is our estimate
    return h

def process_image_with_calibration(image_path, calibration):
    """
    Process the image with the given calibration to extract measurements.
    This is where you would call your actual measurement algorithm.
    For now, we'll return mock measurements scaled by the calibration factor.
    """
    # Get base measurements in pixels or arbitrary units
    base_measurements = mock_base_measurements()
    
    # Get calibration factor
    factor = calibration["factor"]
    
    # Scale measurements by calibration factor to get real-world units (cm)
    measurements = {}
    for key, value in base_measurements.items():
        measurements[key] = round(value * factor, 1)
    
    return measurements

def mock_base_measurements():
    """
    Generate mock base measurements (in arbitrary units).
    These will be scaled by the calibration factor to get real-world units.
    """
    return {
        "height": 1755,
        "shoulder_width": 457,
        "chest_circumference": 982,
        "waist_circumference": 846,
        "hip_circumference": 1023,
        "inseam": 815,
        "arm_length": 658,
        "neck_circumference": 389,
        "shoulder_to_waist": 432,
        "waist_to_hip": 221,
        "thigh_circumference": 587,
        "calf_circumference": 364,
        "bicep_circumference": 328,
        "wrist_circumference": 165
    }

if __name__ == "__main__":
    sys.exit(main()) 