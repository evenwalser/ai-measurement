document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const imageUpload = document.getElementById('imageUpload');
    const previewImage = document.getElementById('previewImage');
    const referenceObject = document.getElementById('referenceObject');
    const customDimensions = document.getElementById('customDimensions');
    const resultsContainer = document.getElementById('resultsContainer');
    const apiResponse = document.getElementById('apiResponse');
    
    // Calibration method elements
    const calibrationMethod = document.getElementById('calibrationMethod');
    const referenceObjectContainer = document.getElementById('referenceObjectContainer');
    const heightCalibrationContainer = document.getElementById('heightCalibrationContainer');
    const spatialCalibrationContainer = document.getElementById('spatialCalibrationContainer');
    const useSpatial = document.getElementById('useSpatial');
    
    // Instruction elements
    const uploadInstructions = document.getElementById('uploadInstructions');
    const realTimeInstructions = document.getElementById('realTimeInstructions');

    // Detect device capabilities
    const deviceCapabilities = detectDeviceCapabilities();
    
    // Configure UI based on device capabilities
    configureUI(deviceCapabilities);

    // Show/hide custom dimensions based on reference selection
    referenceObject.addEventListener('change', function() {
        if (this.value === 'custom') {
            customDimensions.classList.remove('d-none');
        } else {
            customDimensions.classList.add('d-none');
        }
    });

    // Handle calibration method changes
    calibrationMethod.addEventListener('change', function() {
        // Hide all calibration containers
        referenceObjectContainer.classList.add('d-none');
        heightCalibrationContainer.classList.add('d-none');
        spatialCalibrationContainer.classList.add('d-none');
        customDimensions.classList.add('d-none');
        
        // Show the selected container
        switch(this.value) {
            case 'reference':
                referenceObjectContainer.classList.remove('d-none');
                if (referenceObject.value === 'custom') {
                    customDimensions.classList.remove('d-none');
                }
                useSpatial.value = '0';
                break;
            case 'height':
                heightCalibrationContainer.classList.remove('d-none');
                useSpatial.value = '0';
                break;
            case 'spatial':
                spatialCalibrationContainer.classList.remove('d-none');
                useSpatial.value = '1';
                break;
        }
    });

    // Preview image when selected
    imageUpload.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                previewImage.src = e.target.result;
                previewImage.classList.remove('d-none');
            }
            reader.readAsDataURL(file);
            
            // Update UI based on image source
            const source = detectImageSource(this);
            uploadForm.dataset.imageSource = source;
            updateRecommendations(source, deviceCapabilities);
        }
    });

    // Handle form submission
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const selectedMethod = calibrationMethod.value;
        
        // Validate based on selected method
        if (selectedMethod === 'reference') {
            if (referenceObject.value === 'custom') {
                const customWidth = document.getElementById('customWidth').value;
                const customHeight = document.getElementById('customHeight').value;
                
                if (!customWidth || !customHeight) {
                    alert('Please enter custom dimensions');
                    return;
                }
            }
        } else if (selectedMethod === 'height') {
            const personHeight = document.getElementById('personHeight').value;
            
            if (!personHeight) {
                alert('Please enter your height');
                return;
            }
        } else if (selectedMethod === 'spatial') {
            // Set use_spatial to true
            formData.set('use_spatial', '1');
            
            // If device doesn't support LiDAR but user selected spatial, show error
            if (!deviceCapabilities.hasLidar) {
                alert('Your device does not support LiDAR. Please choose another calibration method.');
                return;
            }
        }
        
        // Add device capabilities to request
        formData.append('device_platform', deviceCapabilities.platform);
        formData.append('has_lidar', deviceCapabilities.hasLidar ? '1' : '0');
        formData.append('image_source', uploadForm.dataset.imageSource || 'unknown');
        
        // Display loading state
        resultsContainer.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div><p class="mt-2">Processing image...</p></div>';
        apiResponse.textContent = 'Processing...';
        
        // Send API request
        fetch('/api/v1/measurements', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            // Display raw API response
            apiResponse.textContent = JSON.stringify(data, null, 2);
            
            // Display formatted results
            if (data.success) {
                displayMeasurements(data.measurements);
                
                // Show calibration method used if different from selected
                if (data.method_used && data.method_used !== selectedMethod) {
                    resultsContainer.insertAdjacentHTML('afterbegin', 
                        `<div class="alert alert-info">
                            <strong>Note:</strong> Measurements calculated using ${formatMethodName(data.method_used)} method.
                         </div>`
                    );
                }
            } else {
                resultsContainer.innerHTML = `<div class="alert alert-danger">${data.message || 'An error occurred'}</div>`;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            resultsContainer.innerHTML = '<div class="alert alert-danger">Request failed. Please try again.</div>';
            apiResponse.textContent = 'Request failed: ' + error.message;
        });
    });
    
    // Function to display formatted measurements
    function displayMeasurements(measurements) {
        if (!measurements) {
            resultsContainer.innerHTML = '<div class="alert alert-warning">No measurements returned</div>';
            return;
        }
        
        let html = '<table class="table">';
        html += '<thead><tr><th>Measurement</th><th>Value</th></tr></thead><tbody>';
        
        for (const [key, value] of Object.entries(measurements)) {
            // Format the measurement name (convert snake_case to Title Case)
            const formattedName = key
                .split('_')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(' ');
            
            html += `<tr><td>${formattedName}</td><td>${value} cm</td></tr>`;
        }
        
        html += '</tbody></table>';
        resultsContainer.innerHTML = html;
    }
    
    // Function to detect device capabilities
    function detectDeviceCapabilities() {
        const capabilities = {
            hasLidar: false,
            platform: 'unknown',
            isUpload: false
        };
        
        // Detect platform
        const userAgent = navigator.userAgent;
        if (/android/i.test(userAgent)) {
            capabilities.platform = 'android';
        } else if (/iPad|iPhone|iPod/.test(userAgent)) {
            capabilities.platform = 'ios';
            
            // Check for LiDAR-capable iOS devices
            const lidarDevices = [
                'iPhone12,2', 'iPhone12,3', // iPhone 12 Pro/Pro Max
                'iPhone13,2', 'iPhone13,3', // iPhone 13 Pro/Pro Max
                'iPhone14,2', 'iPhone14,3', // iPhone 14 Pro/Pro Max
                'iPhone15,2', 'iPhone15,3', // iPhone 15 Pro/Pro Max
                'iPad8,', 'iPad13,'         // iPad Pro 2020+
            ];
            
            capabilities.hasLidar = lidarDevices.some(device => userAgent.includes(device));
        } else if (/Windows|Mac|Linux/.test(userAgent)) {
            capabilities.platform = 'desktop';
            capabilities.isUpload = true; // Desktop is always upload
        }
        
        return capabilities;
    }
    
    // Configure UI based on device capabilities
    function configureUI(capabilities) {
        // Add capabilities as data attributes to form
        uploadForm.dataset.platform = capabilities.platform;
        uploadForm.dataset.hasLidar = capabilities.hasLidar;
        uploadForm.dataset.isUpload = capabilities.isUpload;
        
        // Handle LiDAR availability
        if (!capabilities.hasLidar) {
            // Hide spatial option
            document.getElementById('spatialOption').classList.add('d-none');
        }
        
        // Show appropriate instructions
        if (capabilities.isUpload || capabilities.platform === 'desktop') {
            uploadInstructions.classList.remove('d-none');
            realTimeInstructions.classList.add('d-none');
            
            // Pre-select reference object for uploads
            calibrationMethod.value = 'reference';
        } else {
            uploadInstructions.classList.add('d-none');
            realTimeInstructions.classList.remove('d-none');
            
            // Pre-select height-based for mobile real-time capture
            calibrationMethod.value = 'height';
        }
        
        // Trigger UI update based on initial selection
        calibrationMethod.dispatchEvent(new Event('change'));
    }
    
    // Detect if image is an upload vs real-time capture
    function detectImageSource(imageInput) {
        // If we're on mobile and using the file input directly,
        // we can check if the file was just created
        
        const file = imageInput.files[0];
        if (!file) return 'unknown';
        
        const currentTime = new Date();
        const fileModTime = new Date(file.lastModified);
        const timeDiff = currentTime - fileModTime;
        
        // If file was created within the last minute, likely a fresh capture
        // Otherwise probably an upload from gallery
        if (timeDiff < 60000) { // 60 seconds
            return 'real-time';
        } else {
            return 'upload';
        }
    }
    
    // Update recommendations based on image source
    function updateRecommendations(source, capabilities) {
        // Clear previous recommendations
        document.querySelectorAll('.recommendation-alert').forEach(el => el.remove());
        
        let recommendationHtml = '';
        let recommendedMethod = '';
        
        if (source === 'upload' && !capabilities.hasLidar) {
            // For uploads without LiDAR, reference object is recommended
            recommendationHtml = `
                <div class="alert alert-success recommendation-alert mt-2">
                    <strong>Recommended:</strong> For uploaded images, using a reference object provides the most accurate measurements.
                </div>
            `;
            recommendedMethod = 'reference';
        } else if (source === 'real-time' && !capabilities.hasLidar) {
            // For real-time without LiDAR, height can work well
            recommendationHtml = `
                <div class="alert alert-success recommendation-alert mt-2">
                    <strong>Recommended:</strong> For real-time captures on your device, height-based calibration works well.
                </div>
            `;
            recommendedMethod = 'height';
        } else if (capabilities.hasLidar) {
            // For LiDAR devices, spatial is best
            recommendationHtml = `
                <div class="alert alert-success recommendation-alert mt-2">
                    <strong>Recommended:</strong> Your device supports LiDAR - spatial calibration will provide the most accurate results.
                </div>
            `;
            recommendedMethod = 'spatial';
        }
        
        // Add recommendation to the form
        if (recommendationHtml) {
            uploadForm.insertAdjacentHTML('beforeend', recommendationHtml);
            
            // Auto-select the recommended method
            calibrationMethod.value = recommendedMethod;
            calibrationMethod.dispatchEvent(new Event('change'));
        }
    }
    
    // Format method name for display
    function formatMethodName(method) {
        switch(method) {
            case 'reference':
                return 'reference object';
            case 'height':
                return 'height-based';
            case 'spatial':
                return 'spatial (LiDAR)';
            default:
                return method;
        }
    }
}); 