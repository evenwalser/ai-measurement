/**
 * LiDAR Capture Module
 * Handles capturing depth data from WebXR/ARKit on compatible iOS devices.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const startLidarButton = document.getElementById('startLidarCapture');
    const depthPreview = document.getElementById('depthPreview');
    const depthMapData = document.getElementById('depthMapData');
    const hasLidar = document.getElementById('hasLidar');
    
    // Check if AR is supported
    let isArSupported = false;
    
    // Check for WebXR support with depth sensing
    if (navigator.xr) {
        navigator.xr.isSessionSupported('immersive-ar')
            .then(supported => {
                if (supported) {
                    isArSupported = true;
                    console.log('WebXR AR is supported');
                } else {
                    console.log('WebXR AR is not supported');
                    disableLidarCapture();
                }
            })
            .catch(err => {
                console.error('Error checking WebXR support:', err);
                disableLidarCapture();
            });
    } else {
        console.log('WebXR is not supported');
        disableLidarCapture();
    }
    
    // Handle LiDAR checkbox change
    if (hasLidar) {
        hasLidar.addEventListener('change', function() {
            if (this.checked && !isArSupported) {
                alert('Your device does not support LiDAR capture. Please use a different calibration method.');
                this.checked = false;
            }
        });
    }
    
    // Handle Start LiDAR Capture button click
    if (startLidarButton) {
        startLidarButton.addEventListener('click', startLidarCapture);
    }
    
    /**
     * Disable LiDAR capture option
     */
    function disableLidarCapture() {
        if (hasLidar) {
            hasLidar.disabled = true;
            
            // Create a message
            const message = document.createElement('div');
            message.className = 'alert alert-warning mt-2';
            message.innerHTML = 'LiDAR capture is not supported on this device.';
            
            hasLidar.parentNode.appendChild(message);
        }
    }
    
    /**
     * Start LiDAR depth capture using WebXR
     */
    function startLidarCapture() {
        if (!navigator.xr) {
            alert('WebXR is not supported on this device.');
            return;
        }
        
        startLidarButton.disabled = true;
        startLidarButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting capture...';
        
        // Request an AR session
        navigator.xr.requestSession('immersive-ar', {
            requiredFeatures: ['depth-sensing'],
            depthSensing: {
                usagePreference: ['cpu-optimized'],
                dataFormatPreference: ['luminance-alpha']
            }
        }).then(session => {
            console.log('AR session started');
            
            // Set up the session
            setupARSession(session);
            
            // Show depth preview canvas
            depthPreview.classList.remove('hidden');
            
            // Update button
            startLidarButton.innerHTML = '<i class="fas fa-stop-circle"></i> Stop Capture';
            startLidarButton.disabled = false;
            
            // Change button click handler
            startLidarButton.removeEventListener('click', startLidarCapture);
            startLidarButton.addEventListener('click', () => endARSession(session));
            
        }).catch(err => {
            console.error('Error starting AR session:', err);
            alert('Failed to start LiDAR capture: ' + err.message);
            
            startLidarButton.disabled = false;
            startLidarButton.innerHTML = '<i class="fas fa-camera-retro"></i> Start LiDAR Capture';
        });
    }
    
    /**
     * Set up the AR session for depth capture
     * @param {XRSession} session - The WebXR session
     */
    function setupARSession(session) {
        // Create an XR reference space
        session.requestReferenceSpace('viewer').then(referenceSpace => {
            // Create an XR depth data source
            session.updateDepthSensing({
                usagePreference: ['cpu-optimized'],
                dataFormatPreference: ['luminance-alpha']
            });
            
            // Set up session frame callback
            session.requestAnimationFrame((time, frame) => {
                onXRFrame(time, frame, session, referenceSpace);
            });
        });
    }
    
    /**
     * Handle XR frame updates
     */
    function onXRFrame(time, frame, session, referenceSpace) {
        // Request the next frame
        session.requestAnimationFrame((time, frame) => {
            onXRFrame(time, frame, session, referenceSpace);
        });
        
        // Get the depth data
        const depthData = frame.getDepthInformation(referenceSpace);
        
        if (depthData) {
            // Process the depth data
            processDepthData(depthData, session);
        }
    }
    
    /**
     * Process depth data from ARKit
     * @param {XRDepthInformation} depthData - The depth data from WebXR
     * @param {XRSession} session - The WebXR session
     */
    function processDepthData(depthData, session) {
        // Extract depth data
        const width = depthData.width;
        const height = depthData.height;
        const depthArray = new Float32Array(depthData.data.buffer);
        
        // Convert depth data to a visualization for the preview
        renderDepthToCanvas(depthArray, width, height);
        
        // Create JSON representation of depth data for API submission
        const depthDataJson = {
            width: width,
            height: height,
            data: Array.from(depthArray),
            intrinsics: depthData.intrinsics,
            timestamp: Date.now()
        };
        
        // Store depth data for form submission
        depthMapData.value = JSON.stringify(depthDataJson);
    }
    
    /**
     * Render depth data to a canvas as a heatmap visualization
     * @param {Float32Array} depthArray - The depth data array
     * @param {number} width - The width of the depth map
     * @param {number} height - The height of the depth map
     */
    function renderDepthToCanvas(depthArray, width, height) {
        if (!depthPreview) return;
        
        // Set canvas dimensions
        depthPreview.width = width;
        depthPreview.height = height;
        
        const ctx = depthPreview.getContext('2d');
        const imageData = ctx.createImageData(width, height);
        
        // Find min and max depth values for normalization
        let minDepth = Infinity;
        let maxDepth = -Infinity;
        
        for (let i = 0; i < depthArray.length; i++) {
            if (depthArray[i] > 0) {  // Ignore invalid depth values (0)
                minDepth = Math.min(minDepth, depthArray[i]);
                maxDepth = Math.max(maxDepth, depthArray[i]);
            }
        }
        
        // Create heatmap visualization
        for (let i = 0; i < depthArray.length; i++) {
            const depth = depthArray[i];
            
            // Convert depth to color (blue-green-red heatmap)
            let r, g, b;
            
            if (depth <= 0) {
                // Invalid depth - black
                r = g = b = 0;
            } else {
                // Normalize depth value
                const normalizedDepth = (depth - minDepth) / (maxDepth - minDepth);
                
                // Create heatmap color
                if (normalizedDepth < 0.5) {
                    // Blue to Green
                    b = 255 * (1 - 2 * normalizedDepth);
                    g = 255 * (2 * normalizedDepth);
                    r = 0;
                } else {
                    // Green to Red
                    b = 0;
                    g = 255 * (2 - 2 * normalizedDepth);
                    r = 255 * (2 * normalizedDepth - 1);
                }
            }
            
            // Set pixel color in image data
            const pixelIndex = i * 4;
            imageData.data[pixelIndex] = r;
            imageData.data[pixelIndex + 1] = g;
            imageData.data[pixelIndex + 2] = b;
            imageData.data[pixelIndex + 3] = 255;  // Alpha (opaque)
        }
        
        // Draw image data to canvas
        ctx.putImageData(imageData, 0, 0);
    }
    
    /**
     * End the AR session
     * @param {XRSession} session - The WebXR session to end
     */
    function endARSession(session) {
        session.end().then(() => {
            console.log('AR session ended');
            
            // Update button
            startLidarButton.innerHTML = '<i class="fas fa-camera-retro"></i> Start LiDAR Capture';
            
            // Change button click handler back
            startLidarButton.removeEventListener('click', () => endARSession(session));
            startLidarButton.addEventListener('click', startLidarCapture);
            
            // Show captured data indicator if we have depth data
            if (depthMapData.value) {
                const successIndicator = document.createElement('div');
                successIndicator.className = 'alert alert-success mt-2';
                successIndicator.innerHTML = '<i class="fas fa-check-circle"></i> Depth data captured successfully';
                
                const container = document.getElementById('lidarCaptureContainer');
                if (container) {
                    // Remove any existing indicator
                    const existingIndicator = container.querySelector('.alert-success');
                    if (existingIndicator) {
                        container.removeChild(existingIndicator);
                    }
                    
                    container.appendChild(successIndicator);
                }
            }
        }).catch(err => {
            console.error('Error ending AR session:', err);
        });
    }
}); 