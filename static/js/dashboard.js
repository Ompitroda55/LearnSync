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
