<?php
// Test file upload handler
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    header('Content-Type: application/json');
    
    // Check if image was uploaded
    if (!isset($_FILES['image']) || $_FILES['image']['error'] !== UPLOAD_ERR_OK) {
        echo json_encode([
            'success' => false,
            'message' => 'No image file uploaded or upload error',
            'files' => $_FILES
        ]);
        exit;
    }

    // Create uploads directory if it doesn't exist
    $upload_dir = __DIR__ . '/uploads';
    if (!file_exists($upload_dir)) {
        mkdir($upload_dir, 0777, true);
    }

    // Save the uploaded file
    $filename = uniqid() . '_' . basename($_FILES['image']['name']);
    $filepath = $upload_dir . '/' . $filename;
    
    if (move_uploaded_file($_FILES['image']['tmp_name'], $filepath)) {
        echo json_encode([
            'success' => true,
            'message' => 'File uploaded successfully',
            'filename' => $filename,
            'filepath' => $filepath
        ]);
    } else {
        echo json_encode([
            'success' => false,
            'message' => 'Failed to move uploaded file',
            'error' => error_get_last()
        ]);
    }
    exit;
}
?>
<!DOCTYPE html>
<html>
<head>
    <title>File Upload Test</title>
</head>
<body>
    <h1>Test File Upload</h1>
    <form method="post" enctype="multipart/form-data">
        <p>
            <label for="image">Select image:</label>
            <input type="file" name="image" id="image">
        </p>
        <p>
            <label for="reference">Reference object:</label>
            <select name="reference" id="reference">
                <option value="card">Credit Card</option>
                <option value="a4">A4 Paper</option>
                <option value="letter">Letter Paper</option>
            </select>
        </p>
        <p>
            <button type="submit">Upload</button>
        </p>
    </form>
</body>
</html> 