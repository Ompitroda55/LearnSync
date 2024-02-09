// Function to toggle active class of side navigation
function toggleActive(event) {
    // Prevent default link behavior
    event.preventDefault();

    // Remove active class from all links
    const links = document.querySelectorAll('.nav-list-item-link');
    links.forEach(link => link.classList.remove('active'));

    // Add active class to the clicked link
    event.currentTarget.classList.add('active');
}

// Script for Pomodoro
const timeDisplayMin = document.getElementById('time-min');
const timeDisplaySec = document.getElementById('time-sec');
const startButton = document.getElementById('start');
const stopButton = document.getElementById('stop');
const resetButton = document.getElementById('reset');

let isWorkTime = true;
let secondsLeft;
let timerInterval;

function updateTime() {
    const minutes = Math.floor(secondsLeft / 60);
    const seconds = secondsLeft % 60;
    timeDisplayMin.textContent = `${minutes.toString().padStart(2, '0')}`;
    timeDisplaySec.textContent = `${seconds.toString().padStart(2, '0')}`;
}

function startTimer() {
    startButton.disabled = true;
    stopButton.disabled = false;
    resetButton.disabled = false;
    const startTime = new Date().getTime();
    const endTime = startTime + (secondsLeft * 1000);
    localStorage.setItem('endTime', endTime);
    timerInterval = setInterval(() => {
        const now = new Date().getTime();
        secondsLeft = Math.round((endTime - now) / 1000);
        updateTime();
        if (secondsLeft <= 0) {
            clearInterval(timerInterval);
            if (isWorkTime) {
                secondsLeft = 300; // 5 minutes break
                isWorkTime = false;
            } else {
                secondsLeft = 1500; // 25 minutes work time
                isWorkTime = true;
            }
            localStorage.removeItem('endTime');
            startButton.disabled = false;
            stopButton.disabled = true;
        }
    }, 1000);
}

function stopTimer() {
    clearInterval(timerInterval);
    startButton.disabled = false;
    stopButton.disabled = true;
}
function resetTimer() {
    clearInterval(timerInterval);
    isWorkTime = true;
    secondsLeft = 1500; // Reset to 25 minutes work time
    updateTime();
    localStorage.removeItem('endTime');
    startButton.disabled = false;
    stopButton.disabled = true;
}

// Check if there's a saved end time in localStorage
const savedEndTime = localStorage.getItem('endTime');
if (savedEndTime) {
    const now = new Date().getTime();
    secondsLeft = Math.round((savedEndTime - now) / 1000);
    if (secondsLeft > 0) {
        startTimer();
    } else {
        localStorage.removeItem('endTime');
    }
} else {
    secondsLeft = 1500; // Default to 25 minutes work time
}

startButton.addEventListener('click', startTimer);
stopButton.addEventListener('click', stopTimer);
resetButton.addEventListener('click', resetTimer);

// 
// Script for Friends Section
// 
async function checkUsername(username) {
    const response = await fetch('/check-username', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `username=${username}`
    });
    const data = await response.json();
    return data.message === 'Username available';
}

async function checkStatus(username) {
    const response = await fetch('/add-friend/{{ user._id }}', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `friend-username=${username}`
    });
    const data = await response.json();
    return data.message;
}

document.querySelector('#add-friend-btn').addEventListener('click', async function (e) {
    e.preventDefault();
    const username = document.querySelector('#friend-username').value;
    // console.log(username)
    const user_id = '{{ user._id }}';
    let alertbox = document.querySelector('#alert-friend-form');
    if (!username) {
        alertbox.style.display = 'flex';
        alertbox.textContent = "Please enter Friends username";
    }
    const isFriendPresent = await checkUsername(username);

    if (isFriendPresent) {
        response = await checkStatus(username);
        console.log(response);
        if (response === 'Friend already in friends list') {
            alertbox.style.display = 'flex';
            alertbox.textContent = "Already you're friends";
        } else if (response === 'Friend Request Sent!') {
            alertbox.style.display = 'flex';
            alertbox.style.backgroundColor = 'var(--feather-green)';
            alertbox.textContent = "Friend Request Sent!";
        } else {
            alertbox.style.display = 'flex';
            alertbox.textContent = "Failed to add friend"
        }
    } else {
        alertbox.style.display = 'flex';
        alertbox.textContent = "Check Friend's Name";
    }
});

// Script for Expanding Notifications
document.addEventListener('click', function (event) {
    if (event.target.closest('.notification')) {
        const notificationActions = event.target.closest('.notification').querySelector('.notification-action');
        if (notificationActions) {
            notificationActions.classList.toggle('show');
        }
    }
});

// 
// Script for Handling Friend Requests
// 
async function acceptFriendRequest(requestId) {
    const response = await fetch(`/accept-friend-request/${requestId}`, {
        method: 'POST'
    });
    const data = await response.json();
    if (response.status === 200) {
        // Handle success, maybe hide the notification or update UI
        console.log(data.message);
    } else {
        // Handle error, maybe show an error message
        console.error(data.message);
    }
}

async function rejectFriendRequest(requestId) {
    const response = await fetch(`/reject-friend-request/${requestId}`, {
        method: 'POST'
    });
    const data = await response.json();
    if (response.status === 200) {
        // Handle success, maybe hide the notification or update UI
        console.log(data.message);
        // Remove the notification from the UI
        const notification = document.querySelector(`.notification[data-request-id="${requestId}"]`);
        notification.style.display = 'none';
    } else {
        // Handle error, maybe show an error message
        console.error(data.message);
    }
}

// 
// Script for handling daily tasks
// 
document.getElementById('addFields').addEventListener('click', function (e) {
    e.preventDefault();
    var taskFields = document.getElementById('taskFields');
    var newTaskField = document.createElement('div');
    newTaskField.innerHTML = `
                        <input type="text" class="task" name="task[]" placeholder="Question">
                    `;
    taskFields.appendChild(newTaskField);
});
