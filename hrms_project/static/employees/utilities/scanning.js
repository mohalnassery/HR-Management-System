// Handle scanning functionality
let currentSide = 'front';
let frontImage = null;
let backImage = null;

async function startScanning() {
    const scanBtn = document.querySelector('.scan-content button');
    const spinner = document.querySelector('.scan-content .spinner');
    const previewContainer = document.querySelector('.scan-preview');
    const previewImages = document.querySelector('.preview-images');
    const scanMode = document.querySelector('input[name="scanMode"]:checked').value;
    
    try {
        // Show loading state
        scanBtn.disabled = true;
        spinner.style.display = 'inline-block';
        
        // Clear previews if starting fresh scan
        if (scanMode !== 'double' || currentSide === 'front') {
            previewImages.innerHTML = '';
        }
        
        // Call scanning endpoint with retry logic
        let retryCount = 0;
        const maxRetries = 3;
        let response;
        
        while (retryCount < maxRetries) {
            try {
                // Get CSRF token from window object or form
                let csrfToken = window.csrfToken || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
                if (!csrfToken) {
                    csrfToken = getCookie('csrftoken');
                }
                
                if (!csrfToken) {
                    throw new Error('CSRF token not found. Please refresh the page.');
                }
                
                response = await fetch(window.scanEndpoint, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        useFeeder: scanMode === 'feeder',
                        currentSide: currentSide
                    }),
                    credentials: 'same-origin'  // Include cookies in request
                });
                
                if (response.ok) {
                    break;
                }
                
                // If scanner is busy, wait and retry
                const errorData = await response.json();
                if (errorData.error && (
                    errorData.error.includes("The parameter is incorrect") ||
                    errorData.error.includes("CoInitialize") ||
                    errorData.error.includes("Exception occurred")
                )) {
                    retryCount++;
                    if (retryCount < maxRetries) {
                        await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second before retry
                        continue;
                    }
                }
                
                throw new Error(errorData.error || 'Failed to scan document');
            } catch (error) {
                if (retryCount === maxRetries - 1) {
                    throw error;
                }
                retryCount++;
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }
        
        const data = await response.json();
        
        if (scanMode === 'double') {
            // Handle two-sided scanning
            if (currentSide === 'front') {
                frontImage = data.images[0];
                await addPreviewImage(frontImage.data, 'Front Side', previewImages);
                
                // Update for back side
                currentSide = 'back';
                updateScanInstructions();
                scanBtn.innerHTML = 'Scan Back Side <span class="spinner" style="display: none;"><i class="fas fa-spinner fa-spin"></i></span>';
                
            } else {
                backImage = data.images[0];
                await addPreviewImage(backImage.data, 'Back Side', previewImages);
                
                // Create PDF with both sides
                const doc = new window.jspdf.jsPDF();
                doc.addImage(frontImage.data, 'JPEG', 0, 0, 210, 297);
                doc.addPage();
                doc.addImage(backImage.data, 'JPEG', 0, 0, 210, 297);
                
                // Convert to blob and create file
                const pdfBlob = doc.output('blob');
                const file = new File([pdfBlob], "scanned_document.pdf", { type: "application/pdf" });
                
                // Update file input
                updateFileInput(file);
                
                // Reset for next scan
                currentSide = 'front';
                scanBtn.innerHTML = 'Start Scanning <span class="spinner" style="display: none;"><i class="fas fa-spinner fa-spin"></i></span>';
                updateScanInstructions();
            }
            
        } else {
            // Handle single-side or feeder scanning
            const doc = new window.jspdf.jsPDF();
            let firstPage = true;
            
            for (const image of data.images) {
                if (!firstPage) {
                    doc.addPage();
                }
                doc.addImage(image.data, 'JPEG', 0, 0, 210, 297);
                firstPage = false;
                
                await addPreviewImage(image.data, `Page ${data.images.indexOf(image) + 1}`, previewImages);
            }
            
            // Create file from PDF
            const pdfBlob = doc.output('blob');
            const file = new File([pdfBlob], "scanned_document.pdf", { type: "application/pdf" });
            
            // Update file input
            updateFileInput(file);
        }
        
        // Show preview section
        previewContainer.style.display = 'block';
        
    } catch (error) {
        console.error('Scanning error:', error);
        alert('Error while scanning: ' + error.message + '\nPlease make sure your scanner is properly connected and try again.');
    } finally {
        // Reset loading state
        scanBtn.disabled = false;
        spinner.style.display = 'none';
    }
}

async function addPreviewImage(imageData, label, container) {
    // Create thumbnail
    const thumbnailData = await createThumbnail(imageData);
    
    // Create preview container
    const previewContainer = document.createElement('div');
    previewContainer.className = 'preview-image-container';
    
    // Add page number/label
    const pageNumber = document.createElement('div');
    pageNumber.className = 'page-number';
    pageNumber.textContent = label;
    previewContainer.appendChild(pageNumber);
    
    // Add image
    const img = document.createElement('img');
    img.src = thumbnailData;
    img.alt = label;
    img.setAttribute('data-original', imageData);
    previewContainer.appendChild(img);
    
    container.appendChild(previewContainer);
}

function createThumbnail(imageData, maxWidth = 150, maxHeight = 150) {
    return new Promise((resolve) => {
        const img = new Image();
        img.onload = function() {
            const canvas = document.createElement('canvas');
            let width = img.width;
            let height = img.height;
            
            // Calculate new dimensions
            if (width > height) {
                if (width > maxWidth) {
                    height = Math.round(height * maxWidth / width);
                    width = maxWidth;
                }
            } else {
                if (height > maxHeight) {
                    width = Math.round(width * maxHeight / height);
                    height = maxHeight;
                }
            }
            
            canvas.width = width;
            canvas.height = height;
            
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, width, height);
            
            resolve(canvas.toDataURL('image/jpeg', 0.7));
        };
        img.src = imageData;
    });
}

function updateFileInput(file) {
    const fileInput = document.querySelector('input[type="file"]');
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    fileInput.files = dataTransfer.files;
}

function updateScanInstructions() {
    const mode = document.querySelector('input[name="scanMode"]:checked').value;
    const instructions = document.getElementById('twoSideInstructions');
    
    if (mode === 'double') {
        instructions.classList.add('active');
        instructions.querySelector('p').innerHTML = `
            <span class="scan-side-indicator">${currentSide === 'front' ? 'Front' : 'Back'} Side:</span> 
            Place the document with the ${currentSide} side facing down on the scanner.
        `;
    } else {
        instructions.classList.remove('active');
    }
}

// Helper function to get cookie by name
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Add event listener for scan mode changes
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('input[name="scanMode"]').forEach(radio => {
        radio.addEventListener('change', updateScanInstructions);
    });
});
