// document.addEventListener('DOMContentLoaded', function () {
//     const formSteps = document.querySelectorAll('.form-step');
//     let currentStep = 0;
//     updateNavButtons();

//     document.querySelector('#prev-button').addEventListener('click', function (e) {
//         e.preventDefault();
//         currentStep = Math.max(0, currentStep - 1);
//         updateNavButtons();
//     });

//     document.querySelector('#next-button').addEventListener('click', function (e) {
//         e.preventDefault();
//         currentStep = Math.min(formSteps.length - 1, currentStep + 1);
//         updateNavButtons();
//     });

//     function updateNavButtons() {
//         formSteps.forEach((step, index) => {
//             step.style.display = index === currentStep ? 'flex' : 'none';
//         });

//         document.querySelector('#prev-button').disabled = currentStep === 0;
//         document.querySelector('#next-button').disabled = currentStep === formSteps.length - 1;
//     }

// });

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

        const prevButton = document.querySelector('#prev-button');
        const nextButton = document.querySelector('#next-button');
        const signupLinkButton = document.querySelector('#signup-link');

        prevButton.disabled = currentStep === 0;
        nextButton.disabled = currentStep === formSteps.length - 1;

        if (currentStep === formSteps.length - 1) {
            signupLinkButton.disabled = false;
        } else {
            signupLinkButton.disabled = true;
        }
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

async function checkEmail(email) {
    const response = await fetch('/check-email-availability', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `email=${email}`
    });
    const data = await response.json();
    return data.message === 'Email available';
}

async function verifyEmail(email) {
    const response = await fetch('/send-verification-email', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: email })
    });
    const data = await response.json();
    alert(data.otp);
    return data;
}

function verifyOtp(otp) {
    document.getElementById('otp-field').style.display = 'block';
    document.getElementById('verify-otp').style.display = 'block';
    document.getElementById('signup-link').style.display = 'none';
    
    document.getElementById('verify-otp').addEventListener('click', function() {
        const enteredOTP = parseInt(document.getElementById('otp-field').value);
        const actualOTP = parseInt(otp); // Assuming `otp` is a global variable containing the actual OTP
        // console.log(enteredOTP);
        // console.log(actualOTP);
        if (enteredOTP == actualOTP) {
            // OTP verification successful
            // Perform actions such as enabling signup or moving to the next step
            document.getElementById('signup-form').submit();  
        } else {
            // OTP verification failed
            // Show error message or take appropriate action
            console.log(enteredOTP);
            console.log(actualOTP);
        }
    });
}

document.querySelector('#signup-link').addEventListener('click', async function (e) {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const not_pass = document.getElementById('not-pass').value;
    const email = document.getElementById('email').value;
    const isUsernameAvailable = await checkUsername(username);
    const isEmailAvailable = await checkEmail(email);
    
    if (isEmailAvailable && isUsernameAvailable && password === not_pass) { console.log('Username is available and passwords match. Submitting form...');}

    if (isEmailAvailable && isUsernameAvailable && password === not_pass) {
        const otp = await verifyEmail(email);
        document.getElementById('signup-link').style.display = 'none'; // Hide the signup link
        document.getElementById('email').style.display = 'none'; // Hide the signup form
        document.getElementById('otp-field').style.display = 'block'; // Show the OTP field
        document.getElementById('verify-otp').style.display = 'block';
        verifyOtp(otp);
        
    } else if (!isUsernameAvailable) {
        alert('Username already exists. Please choose a different username.');
    } else if (!isEmailAvailable) {
        alert('Email already exists. Please choose a different email.');
    } else if (password !== not_pass) {
        alert('Passwords do not match. Please re-enter your passwords.');
    }
});

