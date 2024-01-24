document.getElementById('open-login').addEventListener('click', function() {
    // Show the overlay
    document.getElementById('login').style.display = 'flex';

    // Disable all focusable elements
    disableFocusableElements(true);
});

document.getElementById('close-login').addEventListener('click', function() {
    // Hide the overlay
    document.getElementById('login-overlay').style.display = 'none';

    // Enable all focusable elements
    disableFocusableElements(false);
});