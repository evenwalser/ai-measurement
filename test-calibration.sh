#!/bin/bash

# Test Script for Body Measurement API Calibration Methods
# This script automates testing of different calibration methods

# Set up color formatting
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================================${NC}"
echo -e "${BLUE}       Body Measurement API Calibration Test Tool       ${NC}"
echo -e "${BLUE}========================================================${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo -e "${RED}Error: Docker is not running. Please start Docker and try again.${NC}"
  exit 1
fi

# Check if test images directory exists
if [ ! -d "test-images" ]; then
  echo -e "${YELLOW}Creating test images directory...${NC}"
  mkdir -p test-images
  echo -e "${GREEN}Please add test images to the test-images directory and run this script again.${NC}"
  exit 0
fi

# Check if we have any test images
if [ -z "$(ls -A test-images)" ]; then
  echo -e "${RED}Error: No test images found in test-images directory.${NC}"
  exit 1
fi

# Ensure the API is running
if ! curl -s http://localhost:8080/api/v1/status.php > /dev/null; then
  echo -e "${YELLOW}Starting the Body Measurement API...${NC}"
  ./start-testing.sh
  
  # Wait for the API to be ready
  attempt=1
  max_attempts=10
  while ! curl -s http://localhost:8080/api/v1/status.php > /dev/null; do
    if [ $attempt -eq $max_attempts ]; then
      echo -e "${RED}Error: Failed to start the API after $max_attempts attempts.${NC}"
      exit 1
    fi
    echo -e "${YELLOW}Waiting for API to start... (attempt $attempt/$max_attempts)${NC}"
    sleep 3
    ((attempt++))
  done
  
  echo -e "${GREEN}API is now running!${NC}"
fi

# Create a results directory
results_dir="test-results/$(date '+%Y%m%d_%H%M%S')"
mkdir -p "$results_dir"

echo "Results will be stored in: $results_dir"
echo ""

# Test different calibration methods for each image
test_methods() {
  local image_path=$1
  local image_name=$(basename "$image_path")
  local result_file="$results_dir/${image_name%.*}_results.json"
  
  echo -e "${BLUE}Testing with image: ${image_name}${NC}"
  
  # Test Height-based Calibration
  echo -e "${YELLOW}Testing Height-based Calibration...${NC}"
  height_result=$(curl -s -F "image=@$image_path" \
                        -F "calibration_method=height" \
                        -F "person_height=175" \
                        -F "device_platform=test" \
                        -F "has_lidar=0" \
                        -F "image_source=upload" \
                        http://localhost:8080/api/v1/measurements)
  
  # Test Reference Object Calibration
  echo -e "${YELLOW}Testing Reference Object Calibration...${NC}"
  reference_result=$(curl -s -F "image=@$image_path" \
                           -F "calibration_method=reference" \
                           -F "reference_object=a4_paper" \
                           -F "device_platform=test" \
                           -F "has_lidar=0" \
                           -F "image_source=upload" \
                           http://localhost:8080/api/v1/measurements)
  
  # Test Spatial Calibration (mock)
  echo -e "${YELLOW}Testing Spatial Calibration (mock)...${NC}"
  spatial_result=$(curl -s -F "image=@$image_path" \
                         -F "calibration_method=spatial" \
                         -F "device_platform=ios" \
                         -F "has_lidar=1" \
                         -F "image_source=upload" \
                         http://localhost:8080/api/v1/measurements)
  
  # Save the results
  echo "{
  \"filename\": \"$image_name\",
  \"timestamp\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",
  \"results\": {
    \"height_based\": $height_result,
    \"reference_object\": $reference_result,
    \"spatial\": $spatial_result
  }
}" > "$result_file"
  
  # Extract the measurements for comparison
  height_success=$(echo "$height_result" | grep -o '"success":[^,]*' | cut -d: -f2)
  reference_success=$(echo "$reference_result" | grep -o '"success":[^,]*' | cut -d: -f2)
  spatial_success=$(echo "$spatial_result" | grep -o '"success":[^,]*' | cut -d: -f2)
  
  echo ""
  echo -e "${BLUE}Results:${NC}"
  echo -e "Height-based Calibration: ${height_success == "true" ? "${GREEN}Success${NC}" : "${RED}Failed${NC}"}"
  echo -e "Reference Object Calibration: ${reference_success == "true" ? "${GREEN}Success${NC}" : "${RED}Failed${NC}"}"
  echo -e "Spatial Calibration: ${spatial_success == "true" ? "${GREEN}Success${NC}" : "${RED}Failed${NC}"}"
  echo ""
  echo -e "Detailed results saved to: ${result_file}"
  echo ""
}

# Process all images in the test-images directory
echo -e "${BLUE}Starting calibration tests with all images...${NC}"
echo ""

for image in test-images/*; do
  if [[ $image == *.jpg || $image == *.jpeg || $image == *.png ]]; then
    test_methods "$image"
  fi
done

# Generate a comparison report
report_file="$results_dir/comparison_report.md"

echo "# Calibration Methods Comparison Report" > "$report_file"
echo "" >> "$report_file"
echo "Generated at: $(date)" >> "$report_file"
echo "" >> "$report_file"
echo "## Summary" >> "$report_file"
echo "" >> "$report_file"
echo "This report compares measurements obtained using different calibration methods." >> "$report_file"
echo "" >> "$report_file"
echo "### Images Tested" >> "$report_file"
echo "" >> "$report_file"

# Get count of successful tests for each method
height_success_count=0
reference_success_count=0
spatial_success_count=0
total_images=0

for result_file in "$results_dir"/*_results.json; do
  if [ -f "$result_file" ]; then
    image_name=$(basename "$result_file" _results.json)
    
    height_success=$(grep -o '"height_based":.*"success":[^,]*' "$result_file" | grep -o '"success":[^,]*' | cut -d: -f2)
    reference_success=$(grep -o '"reference_object":.*"success":[^,]*' "$result_file" | grep -o '"success":[^,]*' | cut -d: -f2)
    spatial_success=$(grep -o '"spatial":.*"success":[^,]*' "$result_file" | grep -o '"success":[^,]*' | cut -d: -f2)
    
    echo "- $image_name" >> "$report_file"
    
    if [ "$height_success" = "true" ]; then ((height_success_count++)); fi
    if [ "$reference_success" = "true" ]; then ((reference_success_count++)); fi
    if [ "$spatial_success" = "true" ]; then ((spatial_success_count++)); fi
    ((total_images++))
  fi
done

# Add success rate statistics
echo "" >> "$report_file"
echo "### Success Rates" >> "$report_file"
echo "" >> "$report_file"
echo "| Calibration Method | Success Rate |" >> "$report_file"
echo "|-------------------|--------------|" >> "$report_file"
height_rate=$((height_success_count * 100 / total_images))
reference_rate=$((reference_success_count * 100 / total_images))
spatial_rate=$((spatial_success_count * 100 / total_images))
echo "| Height-based | $height_rate% ($height_success_count/$total_images) |" >> "$report_file"
echo "| Reference Object | $reference_rate% ($reference_success_count/$total_images) |" >> "$report_file"
echo "| Spatial (mock) | $spatial_rate% ($spatial_success_count/$total_images) |" >> "$report_file"

# Add conclusion
echo "" >> "$report_file"
echo "## Conclusion" >> "$report_file"
echo "" >> "$report_file"
echo "The most reliable calibration method based on this test is: " >> "$report_file"

# Determine the most reliable method
if [ $height_rate -ge $reference_rate ] && [ $height_rate -ge $spatial_rate ]; then
  most_reliable="Height-based Calibration"
elif [ $reference_rate -ge $height_rate ] && [ $reference_rate -ge $spatial_rate ]; then
  most_reliable="Reference Object Calibration"
else
  most_reliable="Spatial Calibration"
fi

echo "**$most_reliable**" >> "$report_file"

# Display the report location
echo -e "${GREEN}Completed all tests!${NC}"
echo -e "${GREEN}Comparison report generated at: ${report_file}${NC}"
echo ""
echo -e "${BLUE}========================================================${NC}" 