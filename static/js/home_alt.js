window.addEventListener('scroll', function () {
    var scrollPosition = window.scrollY;
    var navHeight = document.querySelector('.nav').offsetHeight;
    var navElement = document.querySelector('.nav');

    if (scrollPosition > navHeight) {
        navElement.classList.add('nav-border');
    } else {
        navElement.classList.remove('nav-border');
    }
});

window.addEventListener('scroll', function () {
    var targetElement = document.getElementById('target-1');
    var targetElement1 = document.getElementById('target-2');
    // Get the height from the top of the page
    var elementHeightFromTop = targetElement.offsetTop;
    var elementHeightFromTop1 = targetElement1.offsetTop;

    // Get the current scroll position from the top of the page
    var currentScroll = window.pageYOffset;

    if (currentScroll > elementHeightFromTop - 60 && currentScroll < elementHeightFromTop1 - 60) {
        document.getElementById('top-get-started').style.display = 'block';
    } else {
        document.getElementById('top-get-started').style.display = 'none';
    }
    console.log('Element height from top of the page: ' + elementHeightFromTop + ' pixels');
    console.log('Current scroll position from the top: ' + currentScroll + ' pixels');
});

document.getElementById('open-login').addEventListener('click', function() {
    // Show the overlay
    document.getElementById('login-overlay').style.display = 'flex';

    // Disable all focusable elements
});

document.getElementById('close-login').addEventListener('click', function() {
    // Hide the overlay
    document.getElementById('login-overlay').style.display = 'none';

    // Enable all focusable elements
});

AOS.init();

// Login Logic for Page
async function checkCredentials(username, password) {
    const requestBody = `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`;

    const response = await fetch('/check-credentials', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: requestBody
    });

    const data = await response.json();
    return data.message;
}

document.querySelector('#submit-link').addEventListener('click', async function (e) {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const isCredsValid = await checkCredentials(username, password);
    console.log(isCredsValid);
    const alertBox = document.getElementById('alert-login-form');
    const signupLink = document.getElementById('signup-link');

    if (isCredsValid === 'Valid Creds') {
        document.getElementById('form-login').submit();
    } else if (isCredsValid === 'Incorrect Password') {
        alertBox.style.display = 'flex';
        alertBox.textContent = 'Incorrect Password';
    } else if (isCredsValid === 'Username not available') {
        alertBox.style.display = 'flex';
        alertBox.textContent = 'Username not found';
        // signupLink.style.display = 'flex';
    } else {
        alertBox.style.display = 'flex';
        alertBox.textContent = 'Invalid State! Reload Page.';
    }
});
