<?php
/**
 * Body Measurement API Entry Point
 * 
 * This file serves as the main entry point for the API.
 * It routes requests to the appropriate controllers.
 */

// Enable error reporting in development
if (getenv('APP_ENV') === 'development') {
    ini_set('display_errors', 1);
    ini_set('display_startup_errors', 1);
    error_reporting(E_ALL);
}

// Set content type to JSON by default
header('Content-Type: application/json');

// Include controller
require_once __DIR__ . '/../app/Http/Controllers/MeasurementController.php';

// Parse the request URI
$request_uri = $_SERVER['REQUEST_URI'];
$path = parse_url($request_uri, PHP_URL_PATH);

// Basic routing
if (strpos($path, '/api/v1/measurements') !== false) {
    // Route to measurements endpoint
    $controller = new App\Http\Controllers\MeasurementController();
    
    // Handle request based on method
    switch ($_SERVER['REQUEST_METHOD']) {
        case 'POST':
            $controller->getMeasurements($_POST);
            break;
        case 'OPTIONS':
            // Handle CORS preflight request
            http_response_code(200);
            exit;
        default:
            // Method not allowed
            http_response_code(405);
            echo json_encode([
                'success' => false,
                'message' => 'Method not allowed',
            ]);
            break;
    }
} else {
    // Route not found
    http_response_code(404);
    echo json_encode([
        'success' => false,
        'message' => 'Endpoint not found',
    ]);
} 