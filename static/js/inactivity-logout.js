let inactivityTimer;

const INACTIVITY_LIMIT = 15 * 60 * 1000;
function resetInactivityTimer() {
    clearTimeout(inactivityTimer);

    inactivityTimer = setTimeout(function () {

        // Remove authentication token from browser
        localStorage.removeItem("authToken");

        // Redirect to login page
        window.location.replace("/login/");

    }, INACTIVITY_LIMIT);
}

document.addEventListener("mousemove", resetInactivityTimer);
document.addEventListener("mousedown", resetInactivityTimer);
document.addEventListener("keydown", resetInactivityTimer);
document.addEventListener("scroll", resetInactivityTimer);
document.addEventListener("touchstart", resetInactivityTimer);

resetInactivityTimer();