<?php
/**
 * Body Measurement API Status Endpoint (v1)
 * 
 * This file returns the current status of the API in JSON format.
 */

// Set content type to JSON
header('Content-Type: application/json');

// Get server timestamp
$timestamp = time();

// Generate response
$response = [
    'status' => 'ok',
    'timestamp' => $timestamp,
    'datetime' => date('Y-m-d H:i:s', $timestamp),
    'version' => '1.0.0',
    'api_version' => 'v1',
];

// Convert array to JSON and output
echo json_encode($response); 