# Body Measurement API Testing System

This document outlines the automated testing system implemented for the Body Measurement API.

## Components

The testing system consists of the following components:

1. **Testing Frontend** - A browser-based UI for manual testing
2. **Automated Testing Script** - Shell script for batch testing all calibration methods
3. **Test Data Generator** - Python script to generate mock data for testing
4. **Docker Environment** - Containerized environment for consistent testing

## Testing Frontend

Located in the `testing-frontend/` directory, this browser-based interface allows for:

- Uploading test images
- Selecting calibration methods
- Configuring calibration parameters
- Capturing LiDAR data (on compatible devices)
- Viewing measurement results and visualization
- Inspecting raw API responses

## Automated Testing Script

The `test-calibration.sh` script automates the process of testing multiple images with different calibration methods. It:

- Checks for test images in the `test-images/` directory
- Ensures the API is running
- Processes each image with each calibration method:
  - Height-based calibration
  - Reference object calibration
  - Spatial (LiDAR) calibration
- Saves results to timestamped directories in `test-results/`
- Generates a comparison report of the success rate for each method
- Identifies the most reliable calibration method based on success rates

## Test Data Generator

The `generate-test-data.py` script creates mock data for testing, including:

- Mock depth maps that simulate LiDAR data
- Sample measurement results for validation
- Test data is stored in the `test-data/` directory

## Docker Environment

The `docker-compose.yml` file configures a containerized environment with:

- PHP/Apache container for the API
- Python container for the measurement processing
- Shared volume mounts for test images and results
- Pre-configured for immediate testing

## Testing Workflow

### Manual Testing

1. Run `./start-testing.sh` to start the environment
2. Open `http://localhost:8080/testing-frontend/` in your browser
3. Upload an image and select calibration options
4. Submit the form to process the image
5. View results and API response

### Automated Testing

1. Add test images to the `test-images/` directory
2. Run `./test-calibration.sh` to start batch testing
3. Check `test-results/[timestamp]/comparison_report.md` for results
4. Individual image results are stored as JSON files in the same directory

## Calibration Method Comparison

The testing system automatically compares the success rates of different calibration methods:

- **Height-based Calibration**: Uses the person's height
- **Reference Object Calibration**: Uses a standard object like an A4 paper
- **Spatial Calibration**: Uses LiDAR depth data (currently mocked)

The comparison report includes:
- Success rate for each method
- Per-image success/failure details
- Determination of the most reliable method

## Extending the Testing System

To add new test cases:
1. Add new images to `test-images/`
2. For testing with LiDAR, generate mock depth data using `generate-test-data.py`
3. Run the automated testing script or test manually via the frontend

To add new calibration methods:
1. Update the Python wrapper to include the new method
2. Add appropriate UI elements to the testing frontend
3. Update the automated testing script to include the new method 