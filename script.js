function showMotionPopup() {
    const modal = document.getElementById("motionModal");
    modal.style.display = "block";
    document.getElementById("alertSound").play();
    document.querySelector(".status-text").textContent = "Motion Detected!";
    document.querySelector(".status-text").style.color = "red";
}

function hidePopup() {
    document.getElementById("motionModal").style.display = "none";
}

function handleSave(save) {
    fetch('/save_video', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ save })
    });
    hidePopup();
}

setInterval(() => {
    fetch('/check_motion')
        .then(response => response.json())
        .then(data => {
            if (data.motion) {
                showMotionPopup();
            } else {
                document.querySelector(".status-text").textContent = "No Motion";
                document.querySelector(".status-text").style.color = "lime";
            }
        });
}, 2000);
