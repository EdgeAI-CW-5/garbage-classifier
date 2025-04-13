// Function to fetch and update bin data dynamically
async function updateBinStatus() {
    try {
        const response = await fetch('/api/bin_status');
        const data = await response.json();

        // Loop through the bin status data and update UI
        data.bins.forEach(bin => {
            const statusElement = document.getElementById(`binStatus${bin.id}`);
            if (bin.is_open) {
                statusElement.classList.add('badge-open');
                statusElement.classList.remove('badge-closed');
                statusElement.textContent = 'OPEN';
            } else {
                statusElement.classList.add('badge-closed');
                statusElement.classList.remove('badge-open');
                statusElement.textContent = 'CLOSED';
            }
        });
    } catch (error) {
        console.error("Error fetching bin status:", error);
    }
}

// Function to fetch and update detection data
async function updateDetectionInfo() {
    try {
        const response = await fetch('/api/detection');
        const data = await response.json();

        // Display detected class
        const detectedClassElement = document.getElementById('detectedClass');
        if (data.detected_class) {
            detectedClassElement.textContent = `Detected: ${data.detected_class}`;
        } else {
            detectedClassElement.textContent = 'No Class Detected';
        }

        // Update bin open signals
        const binSignalElement = document.getElementById('binSignal');
        if (data.bin_open_status) {
            binSignalElement.textContent = `Opening: 🚮 ${data.bin_open_status} Bin`;
        }
    } catch (error) {
        console.error("Error fetching detection info:", error);
    }
}

// Call the functions on page load
document.addEventListener("DOMContentLoaded", () => {
    updateBinStatus();
    updateDetectionInfo();
});
