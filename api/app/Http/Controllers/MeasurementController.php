<?php

namespace App\Http\Controllers;

use Exception;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;
use Symfony\Component\Process\Process;
use Symfony\Component\Process\Exception\ProcessFailedException;

class MeasurementController extends Controller
{
    /**
     * Get body measurements from an image
     * 
     * @param Request $request
     * @return \Illuminate\Http\JsonResponse
     */
    public function getMeasurements(Request $request)
    {
        // Validate request
        $validator = validator($request->all(), [
            'image' => 'required|file|image|max:10240',
            'reference_object' => 'nullable|string',
            'reference_width' => 'nullable|numeric',
            'reference_height' => 'nullable|numeric',
            'person_height' => 'nullable|numeric|min:50|max:250',
            'calibration_method' => 'nullable|string|in:reference,height,spatial,direct',
            'calibration_factor' => 'nullable|numeric',
            'has_lidar' => 'nullable|boolean',
            'device_platform' => 'nullable|string',
            'image_source' => 'nullable|string',
            'depth_map_data' => 'nullable|string',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validation failed',
                'errors' => $validator->errors(),
            ], 400);
        }

        // Log request
        Log::info('Measurement request received', [
            'has_image' => $request->hasFile('image'),
            'reference_object' => $request->input('reference_object'),
            'has_lidar' => $request->input('has_lidar'),
            'device_platform' => $request->input('device_platform'),
            'image_source' => $request->input('image_source'),
            'calibration_method' => $request->input('calibration_method'),
        ]);

        // Process image file
        $image = $request->file('image');
        $imagePath = $this->saveImageFile($image);

        // Determine calibration method
        $calibrationMethod = $this->determineCalibrationMethod($request);

        // Process depth map data if available
        $depthMapPath = null;
        if ($request->has('depth_map_data') && !empty($request->input('depth_map_data'))) {
            $depthMapPath = $this->saveDepthMapData($request->input('depth_map_data'));
        }

        // Generate output path for processed image
        $outputPath = storage_path('uploads/' . Str::random(16) . '.jpg');
        
        // Ensure directory exists
        if (!file_exists(dirname($outputPath))) {
            mkdir(dirname($outputPath), 0777, true);
        }

        // Build script arguments based on calibration method
        $args = [];
        
        switch ($calibrationMethod) {
            case 'reference':
                $args = $this->buildReferenceCalibrationArgs($request, $imagePath, $outputPath);
                break;
            case 'height':
                $args = $this->buildHeightCalibrationArgs($request, $imagePath, $outputPath);
                break;
            case 'spatial':
                $args = $this->buildSpatialCalibrationArgs($request, $imagePath, $outputPath, $depthMapPath);
                break;
            case 'direct':
                $args = $this->buildDirectCalibrationArgs($request, $imagePath, $outputPath);
                break;
            default:
                return response()->json([
                    'success' => false,
                    'message' => 'Invalid calibration method',
                ], 400);
        }

        // Execute measurement script
        $result = $this->executeMeasurementScript($args);

        // Return error if script execution failed
        if (!$result['success']) {
            Log::error('Measurement script execution failed', [
                'error' => $result['message'],
                'args' => $this->maskSensitiveData($args),
            ]);
            
            return response()->json([
                'success' => false,
                'message' => 'Measurement processing failed: ' . $result['message'],
            ], 500);
        }

        // Parse script output
        try {
            $measurements = json_decode($result['output'], true);
            
            // Add image URL to the response
            $imageUrl = '/storage/uploads/' . basename($outputPath);
            $measurements['image_url'] = $imageUrl;
            
            return response()->json(array_merge(
                ['success' => true],
                $measurements
            ));
        } catch (Exception $e) {
            Log::error('Failed to parse measurement script output', [
                'error' => $e->getMessage(),
                'output' => $result['output']
            ]);
            
            return response()->json([
                'success' => false,
                'message' => 'Failed to parse measurement results',
                'debug_info' => env('APP_DEBUG') ? $result['output'] : null,
            ], 500);
        }
    }

    /**
     * Save the image file to storage
     * 
     * @param \Illuminate\Http\UploadedFile $image
     * @return string Path to the saved image
     */
    private function saveImageFile($image)
    {
        $fileName = Str::random(16) . '.' . $image->getClientOriginalExtension();
        $path = storage_path('uploads/' . $fileName);
        
        // Ensure directory exists
        if (!file_exists(dirname($path))) {
            mkdir(dirname($path), 0777, true);
        }
        
        $image->move(dirname($path), basename($path));
        
        return $path;
    }

    /**
     * Determine which calibration method to use based on request data
     * 
     * @param Request $request
     * @return string
     */
    private function determineCalibrationMethod(Request $request)
    {
        // If calibration method is explicitly specified, use it
        if ($request->has('calibration_method') && !empty($request->input('calibration_method'))) {
            return $request->input('calibration_method');
        }
        
        // If calibration factor is provided, use direct calibration
        if ($request->has('calibration_factor') && is_numeric($request->input('calibration_factor'))) {
            return 'direct';
        }
        
        // If LiDAR data is available, use spatial calibration
        if ($request->has('has_lidar') && $request->input('has_lidar') && 
            $request->has('depth_map_data') && !empty($request->input('depth_map_data'))) {
            return 'spatial';
        }
        
        // If person height is provided, use height-based calibration
        if ($request->has('person_height') && is_numeric($request->input('person_height'))) {
            return 'height';
        }
        
        // If reference object info is provided, use reference object calibration
        if ($request->has('reference_object') && !empty($request->input('reference_object'))) {
            return 'reference';
        }
        
        // Default to reference object calibration (will require reference object selection)
        return 'reference';
    }

    /**
     * Save depth map data to a temporary file
     * 
     * @param string $depthMapData
     * @return string Path to the saved depth map file
     */
    private function saveDepthMapData($depthMapData)
    {
        $fileName = 'depth_' . Str::random(16) . '.json';
        $path = storage_path('uploads/' . $fileName);
        
        // Ensure directory exists
        if (!file_exists(dirname($path))) {
            mkdir(dirname($path), 0777, true);
        }
        
        // Validate that the depth map data is valid JSON
        $decodedData = json_decode($depthMapData);
        if (json_last_error() !== JSON_ERROR_NONE) {
            throw new Exception('Invalid depth map data format: ' . json_last_error_msg());
        }
        
        file_put_contents($path, $depthMapData);
        
        return $path;
    }

    /**
     * Build arguments for reference object calibration
     * 
     * @param Request $request
     * @param string $imagePath
     * @param string $outputPath
     * @return array
     */
    private function buildReferenceCalibrationArgs(Request $request, $imagePath, $outputPath)
    {
        $args = [
            'python3',
            '/var/www/api/python/wrapper.py',
            '--input', $imagePath,
            '--output', $outputPath,
            '--calibration', 'reference',
        ];
        
        if ($request->has('reference_object') && !empty($request->input('reference_object'))) {
            $args[] = '--reference_object';
            $args[] = $request->input('reference_object');
        }
        
        if ($request->has('reference_width') && is_numeric($request->input('reference_width'))) {
            $args[] = '--reference_width';
            $args[] = $request->input('reference_width');
        }
        
        if ($request->has('reference_height') && is_numeric($request->input('reference_height'))) {
            $args[] = '--reference_height';
            $args[] = $request->input('reference_height');
        }
        
        return $args;
    }

    /**
     * Build arguments for height-based calibration
     * 
     * @param Request $request
     * @param string $imagePath
     * @param string $outputPath
     * @return array
     */
    private function buildHeightCalibrationArgs(Request $request, $imagePath, $outputPath)
    {
        $args = [
            'python3',
            '/var/www/api/python/wrapper.py',
            '--input', $imagePath,
            '--output', $outputPath,
            '--calibration', 'height',
        ];
        
        if ($request->has('person_height') && is_numeric($request->input('person_height'))) {
            $args[] = '--person_height';
            $args[] = $request->input('person_height');
        }
        
        return $args;
    }

    /**
     * Build arguments for spatial calibration
     * 
     * @param Request $request
     * @param string $imagePath
     * @param string $outputPath
     * @param string|null $depthMapPath
     * @return array
     */
    private function buildSpatialCalibrationArgs(Request $request, $imagePath, $outputPath, $depthMapPath = null)
    {
        $args = [
            'python3',
            '/var/www/api/python/wrapper.py',
            '--input', $imagePath,
            '--output', $outputPath,
            '--calibration', 'spatial',
        ];
        
        if ($depthMapPath) {
            $args[] = '--depth_map';
            $args[] = $depthMapPath;
        }
        
        // Add camera intrinsics if available
        if ($request->has('camera_intrinsics') && !empty($request->input('camera_intrinsics'))) {
            $args[] = '--camera_intrinsics';
            $args[] = $request->input('camera_intrinsics');
        }
        
        return $args;
    }

    /**
     * Build arguments for direct calibration
     * 
     * @param Request $request
     * @param string $imagePath
     * @param string $outputPath
     * @return array
     */
    private function buildDirectCalibrationArgs(Request $request, $imagePath, $outputPath)
    {
        $args = [
            'python3',
            '/var/www/api/python/wrapper.py',
            '--input', $imagePath,
            '--output', $outputPath,
            '--calibration', 'direct',
        ];
        
        if ($request->has('calibration_factor') && is_numeric($request->input('calibration_factor'))) {
            $args[] = '--calibration_factor';
            $args[] = $request->input('calibration_factor');
        }
        
        return $args;
    }

    /**
     * Execute the measurement Python script
     * 
     * @param array $args Command arguments
     * @return array Result with success status, output and message
     */
    private function executeMeasurementScript($args)
    {
        // Build command
        $command = implode(' ', array_map('escapeshellarg', $args));
        
        // Set longer timeout for LiDAR processing (120 seconds)
        $timeout = 120;
        
        // Execute command
        $descriptorSpec = [
            0 => ["pipe", "r"],  // stdin
            1 => ["pipe", "w"],  // stdout
            2 => ["pipe", "w"],  // stderr
        ];
        
        $process = proc_open($command, $descriptorSpec, $pipes);
        
        if (!is_resource($process)) {
            return [
                'success' => false,
                'message' => 'Failed to execute measurement script',
            ];
        }
        
        // Close standard input
        fclose($pipes[0]);
        
        // Read standard output
        $output = stream_get_contents($pipes[1]);
        fclose($pipes[1]);
        
        // Read standard error
        $error = stream_get_contents($pipes[2]);
        fclose($pipes[2]);
        
        // Close process
        $exitCode = proc_close($process);
        
        // Log execution
        Log::info('Executed measurement script', [
            'command' => $this->maskSensitiveData($args),
            'exit_code' => $exitCode,
            'error' => $error,
        ]);
        
        if ($exitCode !== 0) {
            return [
                'success' => false,
                'message' => 'Measurement script execution failed: ' . $error,
            ];
        }
        
        return [
            'success' => true,
            'output' => $output,
        ];
    }

    /**
     * Mask sensitive data in logs
     * 
     * @param array $data
     * @return array
     */
    private function maskSensitiveData($data)
    {
        // Create a copy to avoid modifying the original
        $maskedData = $data;
        
        // Find and mask person height
        $personHeightIndex = array_search('--person_height', $maskedData);
        if ($personHeightIndex !== false && isset($maskedData[$personHeightIndex + 1])) {
            $maskedData[$personHeightIndex + 1] = '[MASKED]';
        }
        
        // Find and mask depth map path
        $depthMapIndex = array_search('--depth_map', $maskedData);
        if ($depthMapIndex !== false && isset($maskedData[$depthMapIndex + 1])) {
            $maskedData[$depthMapIndex + 1] = '[MASKED]';
        }
        
        return $maskedData;
    }

    /**
     * Get API status
     *
     * @return \Illuminate\Http\JsonResponse
     */
    public function getStatus()
    {
        return response()->json([
            'status' => 'online',
            'version' => '1.0.0',
            'timestamp' => now()->toIso8601String(),
        ]);
    }
} 