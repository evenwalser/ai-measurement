document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const imageUpload = document.getElementById('imageUpload');
    const previewImage = document.getElementById('previewImage');
    const referenceObject = document.getElementById('referenceObject');
    const customDimensions = document.getElementById('customDimensions');
    const resultsContainer = document.getElementById('resultsContainer');
    const apiResponse = document.getElementById('apiResponse');

    // Show/hide custom dimensions based on reference selection
    referenceObject.addEventListener('change', function() {
        if (this.value === 'custom') {
            customDimensions.classList.remove('d-none');
        } else {
            customDimensions.classList.add('d-none');
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
        }
    });

    // Handle form submission
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        
        // Add custom dimensions if selected
        if (referenceObject.value === 'custom') {
            const customWidth = document.getElementById('customWidth').value;
            const customHeight = document.getElementById('customHeight').value;
            
            if (!customWidth || !customHeight) {
                alert('Please enter custom dimensions');
                return;
            }
        }
        
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
}); 