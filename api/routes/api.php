<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\MeasurementController;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
|
| Here is where you can register API routes for your application. These
| routes are loaded by the RouteServiceProvider within a group which
| is assigned the "api" middleware group. Enjoy building your API!
|
*/

// API Status Route
Route::get('/v1/status.php', [MeasurementController::class, 'getStatus']);

// Body Measurement Routes
Route::post('/v1/measurements', [MeasurementController::class, 'getMeasurements']); 