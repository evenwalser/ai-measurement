# Body Measurement API Documentation

This document provides comprehensive documentation for the Body Measurement API endpoints, including request parameters, response formats, and usage examples.

## Base URL

```
https://api.bodymeasurement.com/api/v1
```

For local development:
```
http://localhost:8080/api/v1
```

## Authentication

Authentication is currently handled through API keys passed in the request header:

```
X-API-Key: your_api_key_here
```

Contact the API administrator to obtain an API key.

## Endpoints

### Status Check

#### `GET /status`

Check if the API is operational.

**Request Headers:**
- `X-API-Key`: Your API key (optional for status endpoint)

**Response:**
```json
{
  "status": "online",
  "version": "1.0.0",
  "timestamp": "2023-06-10T13:45:32Z"
}
```

### Body Measurements

#### `POST /measurements`

Process an image to extract body measurements.

**Request Headers:**
- `X-API-Key`: Your API key (required)
- `Content-Type`: `multipart/form-data`

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image` | File | Yes | The image file to process (JPEG, PNG) |
| `calibration_method` | String | No | Method for calibration: `spatial`, `height`, `reference`, or `direct`. If not provided, the API will choose the best method based on other provided parameters. |
| `person_height` | Number | No* | Person's height in centimeters. *Required if using `height` calibration method. Range: 50-250 cm. |
| `reference_object` | String | No* | Type of reference object visible in the image. *Required if using `reference` calibration method without custom dimensions. Supported values: `a4_paper`, `letter_paper`, `credit_card`, `dollar_bill`, `euro_bill`, `30cm_ruler`. |
| `reference_width` | Number | No* | Width of custom reference object in centimeters. *Required if using `reference` calibration with a custom object. |
| `reference_height` | Number | No* | Height of custom reference object in centimeters. *Required if using `reference` calibration with a custom object. |
| `calibration_factor` | Number | No* | Pre-calculated calibration factor (cm/pixel). *Required if using `direct` calibration method. |
| `has_lidar` | Boolean | No | Whether the device has LiDAR capabilities. Used for device capability detection. |
| `depth_map_data` | String | No* | JSON string containing depth data from LiDAR sensor. *Required if using `spatial` calibration method. See depth map format below. |
| `device_platform` | String | No | Device platform: `ios`, `android`, or `desktop`. Used for analytics and method optimization. |
| `image_source` | String | No | Source of the image: `upload` or `real-time`. Used for analytics and method optimization. |
| `camera_intrinsics` | String | No | JSON string containing camera intrinsic parameters. Improves accuracy for spatial calibration. |

**Depth Map Data Format:**
```json
{
  "width": 256,
  "height": 192,
  "data": [0.1, 0.5, 1.2, ...],
  "timestamp": "2023-06-10T13:45:32Z",
  "intrinsics": {
    "fx": 1.23,
    "fy": 1.23,
    "cx": 128.0,
    "cy": 96.0
  }
}
```

**Camera Intrinsics Format:**
```json
{
  "fx": 1.23,
  "fy": 1.23,
  "cx": 128.0,
  "cy": 96.0
}
```

**Successful Response:**
```json
{
  "success": true,
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
    "method": "spatial",
    "factor": 0.21,
    "confidence": 0.95,
    "unit": "cm/pixel"
  },
  "image_url": "/storage/uploads/processed_image123.jpg",
  "request_id": "a1b2c3d4e5f6",
  "processing_time": 2.35
}
```

**Error Response:**
```json
{
  "success": false,
  "message": "Error processing image",
  "errors": {
    "image": ["The image field is required."],
    "person_height": ["The person height must be between 50 and 250."]
  },
  "request_id": "a1b2c3d4e5f6"
}
```

**Response Status Codes:**

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid or missing API key |
| 413 | Payload Too Large - Image size exceeds limit |
| 415 | Unsupported Media Type - Invalid image format |
| 422 | Unprocessable Entity - Valid request but processing failed |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server-side error |

## Measurement Definitions

The API returns the following measurements (all in centimeters):

| Measurement | Description |
|-------------|-------------|
| `chest` | Circumference of the chest at the widest point |
| `waist` | Circumference of the natural waistline |
| `hips` | Circumference of the hips at the widest point |
| `inseam` | Length from the crotch to the ankle |
| `shoulder_width` | Width across the shoulders from joint to joint |
| `sleeve_length` | Length from shoulder joint to wrist |
| `neck` | Circumference of the neck |

## Calibration Methods

### Spatial Calibration (LiDAR)

Uses depth data from LiDAR sensors available on compatible iOS devices (iPhone Pro models, iPad Pro) to establish real-world scale. This method provides the highest accuracy.

**Required Parameters:**
- `image`
- `depth_map_data`
- `calibration_method`: Set to "spatial"

**Optional Parameters:**
- `camera_intrinsics`: Improves accuracy

### Height-based Calibration

Uses the person's height to establish scale. This method is available on all devices and provides good accuracy when the full body is visible.

**Required Parameters:**
- `image`
- `person_height`: Person's height in centimeters
- `calibration_method`: Set to "height"

### Reference Object Calibration

Uses a known-size object visible in the image to establish scale. This method works well with uploaded images.

**Required Parameters:**
- `image`
- `calibration_method`: Set to "reference"
- Either:
  - `reference_object`: Predefined object type (e.g., "a4_paper")
  - OR both `reference_width` and `reference_height`: Custom dimensions in centimeters

### Direct Calibration

Uses a pre-calculated calibration factor. Useful for applications where calibration has been established by other means.

**Required Parameters:**
- `image`
- `calibration_factor`: Calibration in cm/pixel
- `calibration_method`: Set to "direct"

## Usage Examples

### Example 1: Height-based Calibration

**cURL:**
```bash
curl -X POST "https://api.bodymeasurement.com/api/v1/measurements" \
  -H "X-API-Key: your_api_key_here" \
  -F "image=@person_photo.jpg" \
  -F "calibration_method=height" \
  -F "person_height=175" \
  -F "device_platform=android"
```

### Example 2: Reference Object Calibration

**cURL:**
```bash
curl -X POST "https://api.bodymeasurement.com/api/v1/measurements" \
  -H "X-API-Key: your_api_key_here" \
  -F "image=@person_photo.jpg" \
  -F "calibration_method=reference" \
  -F "reference_object=a4_paper" \
  -F "device_platform=desktop" \
  -F "image_source=upload"
```

### Example 3: Spatial Calibration with LiDAR

**Swift:**
```swift
// Create URL request
let url = URL(string: "https://api.bodymeasurement.com/api/v1/measurements")!
var request = URLRequest(url: url)
request.httpMethod = "POST"
request.addValue("your_api_key_here", forHTTPHeaderField: "X-API-Key")

// Create multipart form data
let boundary = "Boundary-\(UUID().uuidString)"
request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

var body = Data()

// Add image
if let imageData = UIImage(named: "person_photo.jpg")?.jpegData(compressionQuality: 0.8) {
    body.append("--\(boundary)\r\n".data(using: .utf8)!)
    body.append("Content-Disposition: form-data; name=\"image\"; filename=\"person_photo.jpg\"\r\n".data(using: .utf8)!)
    body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
    body.append(imageData)
    body.append("\r\n".data(using: .utf8)!)
}

// Add calibration method
body.append("--\(boundary)\r\n".data(using: .utf8)!)
body.append("Content-Disposition: form-data; name=\"calibration_method\"\r\n\r\n".data(using: .utf8)!)
body.append("spatial\r\n".data(using: .utf8)!)

// Add LiDAR depth data
let depthData = ["width": 256, "height": 192, "data": [/* depth values */], "timestamp": ISO8601DateFormatter().string(from: Date())]
if let depthJSON = try? JSONSerialization.data(withJSONObject: depthData, options: []) {
    let depthString = String(data: depthJSON, encoding: .utf8)!
    body.append("--\(boundary)\r\n".data(using: .utf8)!)
    body.append("Content-Disposition: form-data; name=\"depth_map_data\"\r\n\r\n".data(using: .utf8)!)
    body.append(depthString.data(using: .utf8)!)
    body.append("\r\n".data(using: .utf8)!)
}

// Add device info
body.append("--\(boundary)\r\n".data(using: .utf8)!)
body.append("Content-Disposition: form-data; name=\"device_platform\"\r\n\r\n".data(using: .utf8)!)
body.append("ios\r\n".data(using: .utf8)!)

body.append("--\(boundary)\r\n".data(using: .utf8)!)
body.append("Content-Disposition: form-data; name=\"has_lidar\"\r\n\r\n".data(using: .utf8)!)
body.append("1\r\n".data(using: .utf8)!)

// Final boundary
body.append("--\(boundary)--\r\n".data(using: .utf8)!)

// Create and start task
let task = URLSession.shared.uploadTask(with: request, from: body) { data, response, error in
    guard let data = data, error == nil else {
        print("Error: \(error?.localizedDescription ?? "Unknown error")")
        return
    }
    
    if let jsonResponse = try? JSONSerialization.jsonObject(with: data, options: []) as? [String: Any] {
        print("Response: \(jsonResponse)")
        
        if let measurements = jsonResponse["measurements"] as? [String: Double] {
            print("Chest: \(measurements["chest"] ?? 0) cm")
            print("Waist: \(measurements["waist"] ?? 0) cm")
            // Process other measurements
        }
    }
}

task.resume()
```

### Example 4: JavaScript/Fetch API

```javascript
// Create FormData
const formData = new FormData();
formData.append('image', imageFile);  // From file input
formData.append('calibration_method', 'height');
formData.append('person_height', '180');
formData.append('device_platform', 'desktop');

// Send request
fetch('https://api.bodymeasurement.com/api/v1/measurements', {
  method: 'POST',
  headers: {
    'X-API-Key': 'your_api_key_here'
  },
  body: formData
})
.then(response => {
  if (!response.ok) {
    throw new Error(`HTTP error! Status: ${response.status}`);
  }
  return response.json();
})
.then(data => {
  if (data.success) {
    console.log('Measurements:', data.measurements);
    console.log('Calibration:', data.calibration);
    
    // Display measurements
    document.getElementById('chest').textContent = `${data.measurements.chest} cm`;
    document.getElementById('waist').textContent = `${data.measurements.waist} cm`;
    // Display other measurements
  } else {
    console.error('Error:', data.message);
  }
})
.catch(error => {
  console.error('Fetch error:', error);
});
```

## Rate Limits

The API enforces the following rate limits:

| Plan | Requests per minute | Daily limit |
|------|---------------------|------------|
| Free | 10 | 100 |
| Basic | 60 | 1,000 |
| Pro | 300 | 10,000 |
| Enterprise | Custom | Custom |

When rate limits are exceeded, the API returns a 429 status code with a Retry-After header.

## Error Handling

The API uses standard HTTP status codes and includes detailed error messages in the response body. Always check the `success` field in the response to determine if the request was successful.

Common errors:
- Invalid image (too small, no person detected)
- Missing required parameters
- Invalid calibration method
- Rate limit exceeded
- Internal processing errors

## Best Practices

1. **Image Quality**: 
   - Use well-lit, full-body images
   - Ensure the person is standing straight with arms slightly away from body
   - Avoid loose or baggy clothing for best results

2. **Calibration Method Selection**:
   - For iOS Pro devices with LiDAR: Use spatial calibration
   - For standard mobile devices: Use height-based calibration
   - For uploaded images with reference objects: Use reference object calibration

3. **Error Handling**:
   - Implement proper error handling in your application
   - Provide user-friendly messages for common errors
   - Consider fallback options (e.g., if spatial calibration fails, fall back to height-based)

4. **Performance**:
   - Compress images before uploading for faster processing
   - Use image dimensions of at least 500x500 pixels but not more than 2000x2000 pixels

## Support

For API support, please contact:
- Email: api-support@bodymeasurement.com
- Documentation: https://docs.bodymeasurement.com
- Status page: https://status.bodymeasurement.com 