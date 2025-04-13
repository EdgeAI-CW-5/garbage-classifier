$(document).ready(function () {
    function updateBinStatus() {
        $.ajax({
            url: "/api/bins/status",
            method: "GET",
            dataType: "json",
            success: function (data) {
                updateBinVisuals("bin1", data.bin1);
                updateBinVisuals("bin2", data.bin2);
                updateBinVisuals("bin3", data.bin3);
            },
            error: function (error) {
                console.error("Error fetching bin status:", error);
                updateBinVisuals("bin1", -1);
                updateBinVisuals("bin2", -1);
                updateBinVisuals("bin3", -1);
            }
        });
    }

    function updateBinVisuals(binId, fillPercentage) {
        let progressBar = $("#" + binId + "-progress");
        let percentageSpan = $("#" + binId + "-percentage");
        let fullAlert = $("#" + binId + "-full-alert");
        let binImage = $("#" + binId + "-image");
        let binContainer = $("#" + binId + "-container");
        let fullThreshold = 95;

        if (fillPercentage >= 0) {
            progressBar.css("width", fillPercentage + "%").text(fillPercentage + "%");
            percentageSpan.text(fillPercentage + "%");

            progressBar.removeClass("warning danger");
            if (fillPercentage >= 90) {
                progressBar.addClass("danger");
            } else if (fillPercentage >= 70) {
                progressBar.addClass("warning");
            }

            fullAlert.toggle(fillPercentage >= fullThreshold);

            let imagePath = "";
            if (fillPercentage < 25) {
                imagePath = "bin-empty.png";
            } else if (fillPercentage < 75) {
                imagePath = "bin-medium.png";
            } else {
                imagePath = "bin-full.png";
            }

            binImage.attr("src", "/static/images/" + imagePath);
            binContainer.toggleClass("warning-border", fillPercentage >= fullThreshold);
        } else {
            progressBar.css("width", "100%").text("Error").addClass("danger");
            percentageSpan.text("Error");
            fullAlert.hide();
            binImage.attr("src", "/static/images/bin-error.png");
            binContainer.removeClass("warning-border");
        }
    }

    updateBinStatus();
    setInterval(updateBinStatus, 5000);
});
