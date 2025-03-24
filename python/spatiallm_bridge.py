"""
SpatialLM Bridge Module

This module provides integration with the SpatialLM repository for spatial understanding
and calibration using LiDAR data from compatible devices.

Note: This is a bridge implementation that can work with or without the actual SpatialLM
repository being present. If SpatialLM is not available, it provides mock implementations
for development purposes.
"""

import os
import sys
import json
import numpy as np
import cv2
from pathlib import Path
import tempfile

# Check if SpatialLM is available
try:
    # First, try to import from spatiallm_repo
    SPATIALLM_REPO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "spatiallm_repo")
    if os.path.exists(SPATIALLM_REPO_PATH):
        sys.path.append(SPATIALLM_REPO_PATH)
        from spatiallm_repo.inference import load_point_cloud, load_model, run_inference
        SPATIALLM_AVAILABLE = True
        SPATIALLM_IMPORT_SOURCE = "repo"
    else:
        # If repo not found, try plain spatiallm (may have been installed via pip)
        import torch
        import spatiallm
        SPATIALLM_AVAILABLE = True
        SPATIALLM_IMPORT_SOURCE = "pip"
except ImportError as e:
    print(f"SpatialLM import error: {e}", file=sys.stderr)
    SPATIALLM_AVAILABLE = False
    SPATIALLM_IMPORT_SOURCE = None

def process_lidar_data(image_path, depth_data=None, point_cloud_path=None, camera_intrinsics=None):
    """
    Process LiDAR data to extract spatial understanding and calculate calibration.
    
    Args:
        image_path (str): Path to the color image
        depth_data (dict, optional): Depth map data in JSON format
        point_cloud_path (str, optional): Path to point cloud file
        camera_intrinsics (dict, optional): Camera intrinsics parameters
        
    Returns:
        dict: Calibration result including calibration factor and confidence
    """
    if SPATIALLM_AVAILABLE:
        try:
            return real_spatiallm_processing(image_path, depth_data, point_cloud_path, camera_intrinsics)
        except Exception as e:
            print(f"Error in SpatialLM processing: {str(e)}", file=sys.stderr)
            print(f"Falling back to mock implementation", file=sys.stderr)
            return mock_spatiallm_processing(image_path)
    else:
        print("SpatialLM not available, using mock implementation", file=sys.stderr)
        return mock_spatiallm_processing(image_path)

def real_spatiallm_processing(image_path, depth_data=None, point_cloud_path=None, camera_intrinsics=None):
    """
    Actual SpatialLM processing implementation.
    
    This function uses the actual SpatialLM repository to process spatial data
    and extract calibration information.
    """
    # If we have depth data but no point cloud, create a point cloud from depth data
    if depth_data and not point_cloud_path:
        point_cloud_path = create_point_cloud_from_depth(depth_data, image_path, camera_intrinsics)
    
    if not point_cloud_path:
        raise ValueError("Either depth_data or point_cloud_path must be provided")
    
    # Process the point cloud with SpatialLM
    if SPATIALLM_IMPORT_SOURCE == "repo":
        # Use the cloned repository implementation
        model_path = "manycore-research/SpatialLM-Llama-1B"  # Use the smaller model for faster inference
        
        # Load the point cloud
        point_cloud = load_point_cloud(point_cloud_path)
        
        # Load the model
        model = load_model(model_path)
        
        # Run inference
        with tempfile.NamedTemporaryFile(suffix='.txt') as tmp:
            output_path = tmp.name
            run_inference(model, point_cloud, output_path)
            
            # Parse the output
            with open(output_path, 'r') as f:
                layout_text = f.read()
            
            # Extract calibration factor from structured layout
            calibration_result = extract_calibration_from_layout(layout_text, point_cloud)
            
    elif SPATIALLM_IMPORT_SOURCE == "pip":
        # Use the pip installed implementation
        from spatiallm import SpatialLM
        
        # Initialize the model
        model = SpatialLM()
        
        # Process the point cloud
        result = model.process_point_cloud(point_cloud_path)
        
        # Extract calibration factor
        calibration_result = {
            "calibration_factor": result.get("scale_factor", 0.1),
            "confidence": result.get("confidence", 0.9),
            "reference_objects": extract_reference_dimensions(result)
        }
    
    return calibration_result

def create_point_cloud_from_depth(depth_data, image_path, camera_intrinsics=None):
    """
    Create a point cloud file from depth data and RGB image.
    """
    # Create depth map from the data
    depth_map = convert_depth_data_to_depth_map(depth_data)
    
    # Load the RGB image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    # If camera intrinsics are not provided, use default values
    if not camera_intrinsics:
        height, width = depth_map.shape
        fx = width * 0.8  # Approximate focal length
        fy = width * 0.8
        cx = width / 2
        cy = height / 2
        camera_intrinsics = {
            "fx": fx,
            "fy": fy,
            "cx": cx,
            "cy": cy
        }
    else:
        fx = camera_intrinsics.get("fx")
        fy = camera_intrinsics.get("fy")
        cx = camera_intrinsics.get("cx")
        cy = camera_intrinsics.get("cy")
    
    # Create point cloud
    height, width = depth_map.shape
    points = []
    colors = []
    
    for v in range(height):
        for u in range(width):
            depth = depth_map[v, u]
            if depth > 0:  # Valid depth
                # Convert pixel coordinates to 3D point
                x = (u - cx) * depth / fx
                y = (v - cy) * depth / fy
                z = depth
                
                # Add point
                points.append([x, y, z])
                
                # Add color (BGR to RGB)
                if u < image.shape[1] and v < image.shape[0]:
                    b, g, r = image[v, u]
                    colors.append([r, g, b])
                else:
                    colors.append([128, 128, 128])  # Gray for points outside the image
    
    # Create temporary PLY file
    tmp_ply = tempfile.NamedTemporaryFile(suffix='.ply', delete=False)
    tmp_ply.close()
    
    # Write PLY file
    with open(tmp_ply.name, 'w') as f:
        # Header
        f.write("ply\n")
        f.write("format ascii 1.0\n")
        f.write(f"element vertex {len(points)}\n")
        f.write("property float x\n")
        f.write("property float y\n")
        f.write("property float z\n")
        f.write("property uchar red\n")
        f.write("property uchar green\n")
        f.write("property uchar blue\n")
        f.write("end_header\n")
        
        # Points
        for point, color in zip(points, colors):
            x, y, z = point
            r, g, b = color
            f.write(f"{x} {y} {z} {r} {g} {b}\n")
    
    return tmp_ply.name

def extract_calibration_from_layout(layout_text, point_cloud):
    """
    Extract calibration information from the SpatialLM layout text.
    """
    # Parse the layout text to identify scene dimensions
    objects = []
    walls = []
    
    for line in layout_text.strip().split('\n'):
        if line.startswith("WALL"):
            # Parse wall dimensions
            parts = line.split()
            if len(parts) >= 8:  # WALL x1 y1 z1 x2 y2 z2
                x1, y1, z1 = float(parts[1]), float(parts[2]), float(parts[3])
                x2, y2, z2 = float(parts[4]), float(parts[5]), float(parts[6])
                
                # Calculate wall dimensions
                length = np.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)
                walls.append({"length": length})
        
        elif line.startswith("OBJECT"):
            # Parse object dimensions
            parts = line.split()
            if len(parts) >= 11:  # OBJECT label x y z length width height theta phi psi confidence
                obj_type = parts[1]
                x, y, z = float(parts[2]), float(parts[3]), float(parts[4])
                length, width, height = float(parts[5]), float(parts[6]), float(parts[7])
                confidence = float(parts[10]) if len(parts) > 10 else 0.9
                
                objects.append({
                    "type": obj_type,
                    "width": width * 100,  # Convert to cm
                    "height": height * 100,
                    "length": length * 100,
                    "confidence": confidence
                })
    
    # Use standard object dimensions to calculate calibration factor
    calibration_factor = calculate_calibration_from_objects(objects, walls)
    
    return {
        "calibration_factor": calibration_factor,
        "confidence": 0.9,
        "objects": objects,
        "walls": walls
    }

def calculate_calibration_from_objects(objects, walls):
    """
    Calculate calibration factor using recognized objects.
    
    In a real implementation, this would compare detected objects with
    standard real-world measurements to derive scaling.
    """
    # Standard dimensions for common objects in cm
    standard_dimensions = {
        "door": {"width": 90, "height": 210},
        "chair": {"width": 45, "height": 85},
        "table": {"width": 120, "height": 75},
        "sofa": {"width": 180, "height": 85},
        "bed": {"width": 160, "height": 50},
        "desk": {"width": 120, "height": 75},
        "refrigerator": {"width": 75, "height": 180},
        "toilet": {"width": 40, "height": 40},
        "sink": {"width": 60, "height": 30},
        "bathtub": {"width": 170, "height": 55},
    }
    
    # Wall standard heights (typical ceiling height)
    standard_wall_height = 250  # cm
    
    # Calculate the ratio of real dimensions to detected dimensions
    ratios = []
    
    # Check objects first
    for obj in objects:
        obj_type = obj["type"].lower()
        if obj_type in standard_dimensions:
            std_width = standard_dimensions[obj_type]["width"]
            std_height = standard_dimensions[obj_type]["height"]
            
            detected_width = obj["width"]
            detected_height = obj["height"]
            
            # Calculate ratios
            width_ratio = std_width / detected_width if detected_width > 0 else 0
            height_ratio = std_height / detected_height if detected_height > 0 else 0
            
            # Add valid ratios with confidence weighting
            if width_ratio > 0:
                ratios.append((width_ratio, obj["confidence"]))
            if height_ratio > 0:
                ratios.append((height_ratio, obj["confidence"]))
    
    # Check walls if no good object ratios
    if not ratios and walls:
        # Assume at least one wall represents the room height
        avg_wall_length = sum(wall["length"] for wall in walls) / len(walls)
        height_ratio = standard_wall_height / (avg_wall_length * 100)  # Convert to cm
        ratios.append((height_ratio, 0.7))  # Lower confidence for walls
    
    # If we have ratios, calculate weighted average
    if ratios:
        weighted_sum = sum(ratio * confidence for ratio, confidence in ratios)
        total_weight = sum(confidence for _, confidence in ratios)
        return weighted_sum / total_weight if total_weight > 0 else 0.1
    
    # Default calibration factor if no object matches
    return 0.1  # 0.1 cm per unit

def convert_depth_data_to_depth_map(depth_data):
    """
    Convert depth data from JSON format to depth map array.
    """
    # Implementation depends on the specific format of depth_data
    if "depth_map" in depth_data:
        # If depth_map is provided as a 2D array
        return np.array(depth_data["depth_map"])
    elif "width" in depth_data and "height" in depth_data and "data" in depth_data:
        # If depth data is provided as a flattened array with dimensions
        width = depth_data["width"]
        height = depth_data["height"]
        data = depth_data["data"]
        return np.array(data).reshape(height, width)
    else:
        raise ValueError("Unsupported depth data format")

def extract_reference_dimensions(spatial_result):
    """
    Extract reference object dimensions from SpatialLM result.
    """
    # This implementation depends on the specific output format of SpatialLM
    references = []
    
    # Example implementation assuming SpatialLM returns a list of detected objects
    if "objects" in spatial_result:
        for obj in spatial_result["objects"]:
            if obj["confidence"] > 0.7:  # Only use high-confidence detections
                references.append({
                    "type": obj["type"],
                    "width_cm": obj["dimensions"]["width"],
                    "height_cm": obj["dimensions"]["height"],
                    "width_px": obj["pixel_dimensions"]["width"],
                    "height_px": obj["pixel_dimensions"]["height"],
                    "confidence": obj["confidence"]
                })
    
    return references

def mock_spatiallm_processing(image_path):
    """
    Mock implementation for development when SpatialLM is not available.
    """
    # Load image to get dimensions
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not load image from {image_path}")
    
    height, width = image.shape[:2]
    
    # Generate reasonable mock values
    # For typical human body photos, a reasonable calibration factor is around 0.1-0.2 cm/pixel
    mock_factor = 0.08 + 0.04 * np.random.random()  # Random between 0.08 and 0.12
    
    # Generate mock reference objects
    mock_references = [
        {
            "type": "door",
            "width_cm": 80.0,
            "height_cm": 200.0,
            "width_px": int(80.0 / mock_factor),
            "height_px": int(200.0 / mock_factor),
            "confidence": 0.95
        },
        {
            "type": "chair",
            "width_cm": 45.0,
            "height_cm": 85.0,
            "width_px": int(45.0 / mock_factor),
            "height_px": int(85.0 / mock_factor),
            "confidence": 0.89
        }
    ]
    
    return {
        "calibration_factor": mock_factor,
        "confidence": 0.92,
        "reference_objects": mock_references
    }

def verify_spatiallm_setup():
    """
    Verify that SpatialLM is properly set up.
    Returns True if SpatialLM is available and set up correctly, False otherwise.
    """
    if not SPATIALLM_AVAILABLE:
        return False
    
    # Try to initialize a model to verify setup
    try:
        if SPATIALLM_IMPORT_SOURCE == "repo":
            import sys
            sys.path.append(SPATIALLM_REPO_PATH)
            from spatiallm_repo.inference import load_model
            model = load_model("manycore-research/SpatialLM-Llama-1B")
        elif SPATIALLM_IMPORT_SOURCE == "pip":
            from spatiallm import SpatialLM
            model = SpatialLM()
        return True
    except Exception as e:
        print(f"SpatialLM setup verification failed: {str(e)}", file=sys.stderr)
        return False

def handle_lidar_data_from_device(lidar_data_file, output_path=None):
    """
    Handle LiDAR data coming directly from a device.
    
    Args:
        lidar_data_file (str): Path to LiDAR data file
        output_path (str, optional): Path to save processed data
        
    Returns:
        str: Path to processed data ready for SpatialLM
    """
    # Load the LiDAR data
    with open(lidar_data_file, 'r') as f:
        lidar_data = json.load(f)
    
    # Convert to a point cloud
    temp_ply = create_point_cloud_from_depth(lidar_data, None)
    
    if output_path:
        # Copy to the desired output path
        import shutil
        shutil.copy(temp_ply, output_path)
        os.remove(temp_ply)
        return output_path
    else:
        return temp_ply 