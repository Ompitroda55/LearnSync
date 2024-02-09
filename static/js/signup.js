document.addEventListener('DOMContentLoaded', function () {
    const formSteps = document.querySelectorAll('.form-step');
    let currentStep = 0;
    updateNavButtons();

    document.querySelector('#prev-button').addEventListener('click', function (e) {
        e.preventDefault();
        currentStep = Math.max(0, currentStep - 1);
        updateNavButtons();
    });

    document.querySelector('#next-button').addEventListener('click', function (e) {
        e.preventDefault();
        currentStep = Math.min(formSteps.length - 1, currentStep + 1);
        updateNavButtons();
    });

    function updateNavButtons() {
        formSteps.forEach((step, index) => {
            step.style.display = index === currentStep ? 'flex' : 'none';
        });

        document.querySelector('#prev-button').disabled = currentStep === 0;
        document.querySelector('#next-button').disabled = currentStep === formSteps.length - 1;
    }

});

async function checkUsername(username) {
    const response = await fetch('/check-username-availability', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `username=${username}`
    });
    const data = await response.json();
    return data.message === 'Username available';
}

document.querySelector('#signup-link').addEventListener('click', async function (e) {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const not_pass = document.getElementById('not-pass').value;
    const isUsernameAvailable = await checkUsername(username);
    
    if (isUsernameAvailable && password === not_pass) { console.log('Username is available and passwords match. Submitting form...');}

    if (isUsernameAvailable && password === not_pass) {
        document.getElementById('signup-form').submit();
    } else if (!isUsernameAvailable) {
        alert('Username already exists. Please choose a different username.');
    } else if (password !== not_pass) {
        alert('Passwords do not match. Please re-enter your passwords.');
    }
});