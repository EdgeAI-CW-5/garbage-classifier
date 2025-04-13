let fullBins = {};

function getColorClass(percent) {
    if (percent >= 100) return '#e53935';  // Red color for overflow
    else if (percent >= 75) return '#fbc02d'; // Yellow for high fill
    else return '#43a047'; // Green for low fill
}

// Fetch bin levels from Flask API and update the UI
async function updateBins() {
    try {
        const response = await fetch('/api/bin_levels');
        const data = await response.json();
        
        data.bins.forEach(bin => {
            const percent = bin.fill;
            const id = bin.id;
            const bar = document.getElementById(`bin${id}Fill`);
            const text = document.getElementById(`bin${id}Text`);
            const alertBox = document.getElementById(`alert${id}`);
            const card = document.getElementById(`binCard${id}`);

            // Update progress bar width and color
            bar.style.width = percent + "%";
            bar.innerText = percent + "%";
            text.innerText = "Fill Level: " + percent + "%";
            bar.style.backgroundColor = getColorClass(percent);

            // Show alert if bin is full (>= 90%)
            if (percent >= 90) {
                alertBox.classList.remove("d-none");
                card.classList.add("full");
                fullBins[id] = true;
            } else {
                alertBox.classList.add("d-none");
                card.classList.remove("full");
                fullBins[id] = false;
            }
        });
    } catch (error) {
        console.error("Failed to fetch bin levels:", error);
    }
}

// Open insights page in a new tab
function showInsights(binId) {
    window.open("/insight/" + binId, "_blank");
}

document.addEventListener("DOMContentLoaded", function () {
    updateBins();
    setInterval(updateBins, 5000);  // Update every 5 seconds
});
