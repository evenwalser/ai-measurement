<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Str;

class MeasurementController extends Controller
{
    /**
     * Get the status of the API
     *
     * @return \Illuminate\Http\JsonResponse
     */
    public function status()
    {
        return response()->json([
            'status' => 'online',
            'version' => '1.0.0',
            'timestamp' => now()->toIso8601String()
        ]);
    }

    /**
     * Process an image to get body measurements
     *
     * @param  \Illuminate\Http\Request  $request
     * @return \Illuminate\Http\JsonResponse
     */
    public function processMeasurement(Request $request)
    {
        // Validate the request
        $request->validate([
            'image' => 'required|image|max:10240', // 10MB max
            'reference' => 'required|string|in:card,a4,letter,custom',
        ]);

        if ($request->reference === 'custom') {
            $request->validate([
                'custom_width' => 'required|numeric|min:1',
                'custom_height' => 'required|numeric|min:1',
            ]);
        }

        try {
            // Save uploaded image to storage
            if (!$request->hasFile('image') || !$request->file('image')->isValid()) {
                return response()->json([
                    'success' => false,
                    'message' => 'Invalid image upload'
                ], 400);
            }

            $image = $request->file('image');
            $filename = Str::random(40) . '.' . $image->getClientOriginalExtension();
            $imagePath = public_path('uploads/' . $filename);
            $image->move(public_path('uploads'), $filename);

            // Determine reference object dimensions
            $reference = $request->reference;
            $referenceWidth = 0;
            $referenceHeight = 0;

            switch ($reference) {
                case 'card':
                    $referenceWidth = 85.60;
                    $referenceHeight = 53.98;
                    break;
                case 'a4':
                    $referenceWidth = 210;
                    $referenceHeight = 297;
                    break;
                case 'letter':
                    $referenceWidth = 215.9;
                    $referenceHeight = 279.4;
                    break;
                case 'custom':
                    $referenceWidth = $request->custom_width;
                    $referenceHeight = $request->custom_height;
                    break;
            }

            // Call Python script for measurements
            $command = "cd /var/www/measurement-algorithm && python3 wrapper.py --input {$imagePath} --reference {$reference} --width {$referenceWidth} --height {$referenceHeight} 2>&1";
            
            Log::info("Running command: {$command}");
            $output = shell_exec($command);
            Log::info("Command output: {$output}");

            // Parse the output (assuming the Python script outputs JSON)
            $measurementData = json_decode($output, true);
            
            if (!$measurementData || !isset($measurementData['measurements'])) {
                return response()->json([
                    'success' => false,
                    'message' => 'Failed to process measurements',
                    'debug' => $output
                ], 500);
            }

            return response()->json([
                'success' => true,
                'measurements' => $measurementData['measurements'],
                'image_url' => asset('uploads/' . $filename)
            ]);
        } catch (\Exception $e) {
            Log::error('Measurement processing error: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'message' => 'Error processing image: ' . $e->getMessage()
            ], 500);
        }
    }
} 