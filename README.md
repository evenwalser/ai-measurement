# Human body measurement using computer vision/ 3D modeling
Anthropometric measurement extraction

![alt text](https://github.com/farazBhatti/Human-Body-Measurements-using-Computer-Vision/blob/master/sample_data/input/image_1_50.png)



Accurately obtaining human body measurements from a single image is a challenging task. This repository provides the source code and associated files for a system that leverages computer vision and 3D modeling techniques to achieve precise body part measurements.

The system utilizes OpenCV and TensorFlow for advanced image processing, keypoint detection, and 3D reconstruction. By analyzing a single image of a human subject, it identifies key points and reconstructs a 3D model. This model enables accurate measurements of various body parts, including arm length, waist circumference, and hip width, with results provided in centimeters.

Built on top of the [HMR](https://github.com/akanazawa/hmr) model, this solution serves as a robust starting point for researchers and developers working in this domain. The code has been tested with TensorFlow 1.13.1 for compatibility and reliability.


![alt text](https://github.com/farazBhatti/Human-Body-Measurements-using-Computer-Vision/blob/master/sample_data/input/Screenshot%20from%202021-01-27%2014-34-16.png)

![alt text](https://github.com/farazBhatti/Human-Body-Measurements-using-Computer-Vision/blob/master/sample_data/input/Screenshot%20from%202023-03-28%2020-12-31.png)

###  Download pre-trained model
Type the following command on the terminal to download pre-trained model

`wget https://people.eecs.berkeley.edu/~kanazawa/cachedir/hmr/models.tar.gz && tar -xf models.tar.gz`

and save it in 'models' folder.

### CustomBodyPoints

Download [CustomBodyPoints](https://github.com/farazBhatti/Human-Body-Measurements-using-Computer-Vision/files/5886235/customBodyPoints.txt) text file and place it in the data folder.

### Install Packages

   `pip install -r requirements.txt`
   or
   `pip3 install -r requirements.txt`

## Easy to Run / Jupyter NoteBook / Quick Demo 
A Jupyter notebook has been added and updated for those who quickly want to get inference without much hassle. Simply change the path to your input image.
Thanks to [Hamza Khalil](https://github.com/hamzakhalil798) for adding this notebook.

## Inference
`python3 inference.py -i <path to Image1> -ht <height in cm>`
 
## My LinkedIn
[FarazBhatti](https://www.linkedin.com/in/farazahmadbhatti/)

## Acknowledgment
[HMR](https://github.com/akanazawa/hmr)

[Remove_background](https://github.com/farazBhatti/bg_remove_GUI)

[Deep lab v3 +](https://github.com/rishizek/tensorflow-deeplab-v3)

[Humanbody shape](https://github.com/1900zyh/3D-Human-Body-Shape)

# Body Measurement API

A comprehensive API for extracting accurate body measurements from a single image with multiple calibration methods, designed for cross-platform use including iOS apps with LiDAR capabilities.

## Features

- **Multiple Calibration Methods**:
  - **Spatial Calibration**: Uses LiDAR depth data for highest accuracy (iOS Pro devices)
  - **Height-based Calibration**: Uses person's height for good accuracy
  - **Reference Object Calibration**: Uses known objects like A4 paper or credit cards
  - **Direct Calibration**: Uses pre-calculated calibration factors

- **Cross-Platform Compatibility**:
  - iOS (with special support for LiDAR-capable devices)
  - Android
  - Web browsers

- **Adaptive Processing**:
  - Automatic device capability detection
  - Graceful degradation between calibration methods
  - Detailed measurement results with confidence scores

## Architecture

The system consists of the following components:

| Component | Technology | Description |
|-----------|------------|-------------|
| API Layer | Laravel/PHP | Handles HTTP requests, file uploads, and communicates with the measurement core |
| Measurement Core | Python | Processes images, extracts measurements, and applies calibration |
| Spatial Understanding | SpatialLM | Uses spatial data from LiDAR-capable devices for enhanced accuracy |
| Testing Frontend | HTML/JS | Provides a user interface for testing the API functionality |
| Infrastructure | Docker | Containerized deployment environment |

## Getting Started

### Prerequisites

- Docker and Docker Compose
- PHP 8.1+
- Python 3.9+
- Node.js 14+ (for development)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/body-measurement-api.git
   cd body-measurement-api
   ```

2. Start the Docker environment:
   ```bash
   docker-compose up -d
   ```

3. Access the testing frontend:
   ```
   http://localhost:8080/testing-frontend/
   ```

### Environment Setup

The Docker environment sets up all required dependencies. For local development without Docker:

1. Install PHP dependencies:
   ```bash
   cd api
   composer install
   ```

2. Install Python dependencies:
   ```bash
   pip install numpy opencv-python mediapipe torch torchvision onnx onnxruntime transformers accelerate safetensors
   ```

## API Documentation

### Endpoints

#### `POST /api/v1/measurements`

Process an image to extract body measurements.

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| image | File | Yes | The image to process (JPEG/PNG) |
| calibration_method | String | No | Calibration method to use: 'spatial', 'height', 'reference', or 'direct' |
| person_height | Number | No* | Person's height in cm (required for height-based calibration) |
| reference_object | String | No* | Type of reference object (e.g., 'a4_paper', 'credit_card') |
| reference_width | Number | No* | Width of custom reference object in cm |
| reference_height | Number | No* | Height of custom reference object in cm |
| has_lidar | Boolean | No | Whether the device has LiDAR capabilities |
| depth_map_data | String | No* | JSON string of depth data from LiDAR (required for spatial calibration) |
| calibration_factor | Number | No* | Pre-calculated calibration factor (required for direct calibration) |
| device_platform | String | No | Device platform ('ios', 'android', 'desktop') |

**Response**:

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
  "image_url": "/storage/uploads/processed_image123.jpg"
}
```

### Error Responses

```json
{
  "success": false,
  "message": "Error message",
  "errors": {
    "field_name": ["Validation error message"]
  }
}
```

## Integration with iOS Apps

### iOS Integration Flow

1. **Device Capability Detection**:
   ```swift
   let hasLidar = false
   if #available(iOS 14.0, *) {
       if ARWorldTrackingConfiguration.supportsSceneReconstruction(.mesh) {
           hasLidar = true
       }
   }
   ```

2. **LiDAR Data Capture** (for LiDAR-capable devices):
   ```swift
   // Configure AR session with LiDAR
   let config = ARWorldTrackingConfiguration()
   if ARWorldTrackingConfiguration.supportsFrameSemantics(.sceneDepth) {
       config.frameSemantics.insert(.sceneDepth)
   }
   
   // Start AR session
   arSession.run(config)
   
   // Capture depth data
   func captureDepthData(frame: ARFrame) {
       guard let depthMap = frame.sceneDepth?.depthMap else { return }
       
       // Process depth data
       let width = CVPixelBufferGetWidth(depthMap)
       let height = CVPixelBufferGetHeight(depthMap)
       
       // Convert to data format for API
       let depthData = convertDepthMapToData(depthMap, width: width, height: height)
       
       // JSON encode
       let jsonData = try? JSONEncoder().encode(depthData)
       let jsonString = String(data: jsonData!, encoding: .utf8)!
   }
   ```

3. **API Request Example**:
   ```swift
   let url = URL(string: "https://your-api-url.com/api/v1/measurements")!
   var request = URLRequest(url: url)
   request.httpMethod = "POST"
   
   let boundary = UUID().uuidString
   request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
   
   let body = NSMutableData()
   
   // Add image data
   body.append(/* multipart form data for image */)
   
   // Add parameters
   body.append("--\(boundary)\r\n")
   body.append("Content-Disposition: form-data; name=\"calibration_method\"\r\n\r\n")
   body.append("spatial\r\n")
   
   body.append("--\(boundary)\r\n")
   body.append("Content-Disposition: form-data; name=\"has_lidar\"\r\n\r\n")
   body.append("1\r\n")
   
   body.append("--\(boundary)\r\n")
   body.append("Content-Disposition: form-data; name=\"depth_map_data\"\r\n\r\n")
   body.append(jsonString + "\r\n")
   
   // Complete the request
   body.append("--\(boundary)--\r\n")
   
   // Send request
   let task = URLSession.shared.uploadTask(with: request, from: body as Data) { data, response, error in
       // Handle response
   }
   task.resume()
   ```

## Android Integration

For Android devices (which typically lack LiDAR), use height-based or reference object calibration:

```kotlin
// Example using OkHttp
val client = OkHttpClient()

val requestBody = MultipartBody.Builder()
    .setType(MultipartBody.FORM)
    .addFormDataPart("image", "user_image.jpg", RequestBody.create(MediaType.parse("image/jpeg"), imageFile))
    .addFormDataPart("calibration_method", "height")
    .addFormDataPart("person_height", "175")
    .addFormDataPart("device_platform", "android")
    .build()

val request = Request.Builder()
    .url("https://your-api-url.com/api/v1/measurements")
    .post(requestBody)
    .build()

client.newCall(request).enqueue(object : Callback {
    override fun onResponse(call: Call, response: Response) {
        // Handle successful response
        val responseData = response.body()?.string()
        val measurements = JSONObject(responseData).getJSONObject("measurements")
    }

    override fun onFailure(call: Call, e: IOException) {
        // Handle failure
    }
})
```

## Testing

### Automated Testing

Use the provided test script to run automated tests:

```bash
./test-calibration.sh
```

This will:
1. Process test images with all calibration methods
2. Generate comparison reports
3. Identify the most reliable method

### Manual Testing

Use the testing frontend to manually test different calibration methods:

1. Go to `http://localhost:8080/testing-frontend/`
2. Upload an image
3. Select a calibration method and provide required parameters
4. Submit and view results

## SpatialLM Integration

The Body Measurement API integrates with SpatialLM for advanced 3D scene understanding using LiDAR data. To test this integration:

```bash
python test-spatiallm-integration.py --image test-images/sample.jpg --generate_mock
```

## Development

Consult the `DEVELOPMENT_PLAN.md` file for detailed development roadmap, tasks, and implementation details.

## License

[MIT License](LICENSE)

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a pull request

