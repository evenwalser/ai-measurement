<?php

/**
 * Simple API Router for Body Measurement API
 * 
 * This is a simplified version of a Laravel index.php file
 * for demonstration purposes. In a full Laravel app, this 
 * would be much more complex.
 */

// Set error reporting
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Define the base path
define('BASE_PATH', __DIR__);

// Autoloading for controllers
spl_autoload_register(function ($class) {
    $file = BASE_PATH . '/' . str_replace('\\', '/', $class) . '.php';
    if (file_exists($file)) {
        require $file;
        return true;
    }
    return false;
});

// Basic routing
$request_uri = $_SERVER['REQUEST_URI'];
$method = $_SERVER['REQUEST_METHOD'];

// API route handling
if (strpos($request_uri, '/api/v1/status') !== false && $method === 'GET') {
    header('Content-Type: application/json');
    echo json_encode([
        'status' => 'online',
        'version' => '1.0.0',
        'timestamp' => date('c')
    ]);
    exit;
}

if (strpos($request_uri, '/api/v1/measurements') !== false && $method === 'POST') {
    // Validate that an image was uploaded
    if (!isset($_FILES['image']) || $_FILES['image']['error'] !== UPLOAD_ERR_OK) {
        header('Content-Type: application/json');
        echo json_encode([
            'success' => false,
            'message' => 'No image file uploaded or upload error'
        ]);
        exit;
    }

    // Validate reference object
    if (!isset($_POST['reference'])) {
        header('Content-Type: application/json');
        echo json_encode([
            'success' => false,
            'message' => 'Reference object not specified'
        ]);
        exit;
    }

    try {
        // Create uploads directory if it doesn't exist
        $upload_dir = BASE_PATH . '/uploads';
        if (!file_exists($upload_dir)) {
            mkdir($upload_dir, 0777, true);
        }

        // Save the uploaded file
        $filename = uniqid() . '_' . basename($_FILES['image']['name']);
        $filepath = $upload_dir . '/' . $filename;
        
        if (!move_uploaded_file($_FILES['image']['tmp_name'], $filepath)) {
            throw new Exception('Failed to move uploaded file');
        }

        // Get reference object details
        $reference = $_POST['reference'];
        $reference_width = 0;
        $reference_height = 0;

        switch ($reference) {
            case 'card':
                $reference_width = 85.60;
                $reference_height = 53.98;
                break;
            case 'a4':
                $reference_width = 210;
                $reference_height = 297;
                break;
            case 'letter':
                $reference_width = 215.9;
                $reference_height = 279.4;
                break;
            case 'custom':
                if (!isset($_POST['custom_width']) || !isset($_POST['custom_height'])) {
                    throw new Exception('Custom dimensions not provided');
                }
                $reference_width = floatval($_POST['custom_width']);
                $reference_height = floatval($_POST['custom_height']);
                break;
        }

        // Call the Python script
        $command = "cd /var/www/measurement-algorithm && python3 wrapper.py --input '{$filepath}' --reference {$reference} --width {$reference_width} --height {$reference_height} 2>&1";
        
        $output = shell_exec($command);
        $result = json_decode($output, true);

        if ($result === null) {
            throw new Exception('Failed to process measurements: ' . $output);
        }

        if (isset($result['error'])) {
            throw new Exception($result['error']);
        }

        // Return the results
        header('Content-Type: application/json');
        echo json_encode([
            'success' => true,
            'measurements' => $result['measurements'],
            'image_url' => '/uploads/' . $filename
        ]);
        exit;
    } catch (Exception $e) {
        header('Content-Type: application/json');
        echo json_encode([
            'success' => false,
            'message' => 'Error processing image: ' . $e->getMessage()
        ]);
        exit;
    }
}

// If no routes match, return 404
header('HTTP/1.0 404 Not Found');
header('Content-Type: application/json');
echo json_encode([
    'success' => false,
    'message' => 'Endpoint not found'
]);
exit; 