<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\MeasurementController;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
|
| Here is where you can register API routes for your application.
|
*/

// API Status endpoint
Route::get('/status', [MeasurementController::class, 'status']);

// Measurement endpoint
Route::post('/measurements', [MeasurementController::class, 'processMeasurement']); 