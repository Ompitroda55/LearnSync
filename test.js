document.querySelector('#add-friend-btn').addEventListener('click', async function (e) {
    e.preventDefault();
    const username = document.querySelector('#friend-username').value;
    const user_id = '{{ user._id }}';
    let alertbox = document.querySelector('#alert-friend-form');
    if (!username) {
        alertbox.style.display = 'flex';
        alertbox.textContent = "Please enter Friends username";
    } else {
        const response = await fetch(`/add-friend/${user_id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: `friend-username=${username}`
        });
        const data = await response.json();
        if (response.status == 200) {
            if (data.status === 'available') {
                alertbox.style.display = 'flex';
                alertbox.textContent = data.message;
            } else if (data.status === 'sent') {
                alertbox.style.display = 'flex';
                alertbox.textContent = data.message;
            }
        } else if (response.status == 400) {
            alertbox.style.display = 'flex';
            alertbox.textContent = data.message;
        } else {
            alertbox.style.display = 'flex';
            alertbox.textContent = "Failed to add friend";
        }
    }
});