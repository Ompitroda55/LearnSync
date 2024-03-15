from datetime import datetime
import bcrypt
from bson.objectid import ObjectId
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from flask import Flask, json, jsonify, render_template, request, redirect, session, url_for
import secrets
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random

app = Flask(__name__)

app.secret_key = secrets.token_hex(24)


class User:
    def __init__(self, userId):
        self.userId = userId
        user = db.users.find_one({"_id" : ObjectId(userId)})
        self.user_data = {
            '_id': str(user['_id']),
            'username': user['username'],
            'password': user['password'],
            'stats': [{'streaks': user['stats'][0]['streaks'], 'gems': user['stats'][0]['gems'], 'hearts': user['stats'][0]['hearts']}],
            'groups': user['groups'],
            'friends': user['friends']
        }

user_object = None
# MongoDB Stuff goes here
uri = "mongodb+srv://admin:admin@learnsynccluster.el71bgq.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, server_api=ServerApi('1'))
# client = MongoClient('mongodb://localhost:27017/')
db = client["LearnSyncDatabase"]

# 
# Supporting Functions for Front-end & other Main Func's()
# 

# Function for creating user
def createUser(username, password, email):
    collection = db["users"]
    
    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    new_user = {
        "username": username,
        "password": hashed_password,
        "email": email,
        "stats": [
            {
                "streaks":0,
                "gems":0,
                "hearts":0
            }
        ], 
        "groups": [],
        "friends": [],
        "dailytasks": [
            {
                "task":"Daily Quest",
                "priority":1,
                "completed":0,
                "lastupdate":datetime.now()
            }
        ],
        "pomodoro_sequences":[
            [25.0,5.0,25.0,5.0,25.0,30.0],
            [60.0,10.0,60.0,10.0,60.0,30.0],
            [75.0,15.0,45.0,10.0,30.0,60.0]
        ], "joinging_date" : datetime.now()
        
    }

    new_user = collection.insert_one(new_user)
    return new_user

# Fuction to Create Varous types of request
def createRequest(from_user, to_user, type):
    request_types = {
        0:'Friend Request',
        1:'Streak Request',
        2:'Invite to Group',
        3:'Remove as Friend'
    }
    collection = db['requests']
    new_request = {
        "sender": from_user,
        "receiver": to_user,
        "type" : request_types[type],
        "status": "pending",
        "timestamp" : datetime.now()
    }
    new_request = collection.insert_one(new_request)
    # print(new_request)
    return new_request

def createNotification(from_user, to_user, type, data=None):
    notification_types = {
        0:'Requested Accepted',
        1:'Request Rejected',
        2:'Removed you as a Friend',
        3:'Streak Sent',
        4:'Added you to Group',
        5:'New Task Added to Group',
        6:f"{from_user} removed group - {data}",
        7:"You have been removed from group - {data}"
    }
    collection = db['notifications']
    new_notification = {
        "sender": from_user,
        "receiver": to_user,
        "type" : notification_types[type],
        "status": "pending",
        "timestamp" : datetime.now()
    }
    new_notification = collection.insert_one(new_notification)
    # print(new_request)
    return new_notification

def createGroup(name, leader, members, creation_date):
    members = [leader] + members
    collection = db['groups']
    users_collection = db['users']
    # print(name, leader, members, creation_date)
    new_group = {
        "name": name,
        "group_leader": leader,
        "members": members,
    }

    for member in members:
        users_collection.update_one(
            {"username": member},
            {"$push": {"groups": name}}
        )
        createNotification(leader, member, 4)
    new_group = collection.insert_one(new_group)
    return new_group

@app.route('/add-member-to-group', methods=['POST'])
def insertNewMember():
    try:
        groups_collection = db["groups"]
        # Get the selected friends and groupId from the request
        selected_friends = request.form.get('selectedFriends')
        selected_friends = json.loads(selected_friends)
        print(selected_friends)
        groupId = request.form.get('groupId')

        # Check if the groupId exists in the groups collection
        group = groups_collection.find_one({"_id": ObjectId(groupId)})
        if not group:
            return jsonify({'success': False, 'message': 'Group not found'}), 404

        # Update the group document to add the selected friends to the 'members' array
        members = group.get("members", [])
        for friend in selected_friends:
            if friend not in members:
                members.append(friend)

        # Update the group document with the modified 'members' array
        result = groups_collection.update_one(
            {"_id": ObjectId(groupId)},
            {"$set": {"members": members}}
        )

        # Check if the group document was updated successfully
        if result.modified_count > 0:
            return jsonify({'success': True, 'message': 'Members added successfully'}), 200
        else:
            return jsonify({'success': False, 'message': 'Failed to add members to group'}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/check-username-availability', methods=['POST'])
def check_username_available():
    collection = db["users"]
    username = request.form.get('username')
    user = collection.find_one({'username': username})
    if user:
        return jsonify({'message': 'Username already exists'}), 409
    else:
        return jsonify({'message': 'Username available'}), 200

@app.route('/check-email-availability', methods=['POST'])
def check_email_available():
    collection = db["users"]
    email = request.form.get('email')
    email = collection.find_one({'email': email})
    if email:
        return jsonify({'message': 'Email already exists'}), 409
    else:
        return jsonify({'message': 'Email available'}), 200

@app.route('/check-username', methods=['POST'])
def check_username():
    collection = db["users"]
    username = request.form.get('username')
    user = collection.find_one({'username': username})
    if user:
        return jsonify({'message': 'Username available'}), 200
    else:
        return jsonify({'message': 'Username do not exist'}), 409


# Function for checing if user credentials are valid or not.
@app.route('/check-credentials', methods=['POST'])
def checkCredentials():
    collection = db["users"]
    username = request.form.get('username')
    password = request.form.get('password')
    # print("User password : " + password, username)
    user = collection.find_one({'username': username})
    # print(user['password'])
    if user:
        hashed_password = user['password']
        if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
            return jsonify({'message': 'Valid Creds'}), 200
        else:
            return jsonify({'message': 'Incorrect Password'}), 400
        # if password == user['password']:
        #     return jsonify({'message': 'Valid Creds'}), 200
        # else:
        #     return jsonify({'message': 'Incorrect Password'}), 400
  
    else:
        return jsonify({'message': 'Username not available'}), 400

@app.route('/send-verification-email', methods=['POST'])
def send_verification_email():
    # Get email and generate OTP
    data = request.get_json()
    email = data.get('email')
    # print(email)
    otp = str(random.randint(100000, 999999))

    # Construct HTML content for the email
    subject = 'Email Verification Mail'
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{subject}</title>
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: Arial, sans-serif;
                background-color: #ffffff;
            }}
            .container {{
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                background-color: #58cc02;
                color: #ffffff;
                padding: 20px;
            }}
            .logo {{
                font-size: 2.5rem;
                font-family: 'Varela Round', sans-serif;
                font-weight: 800;
                margin-bottom: 20px;
            }}
            .subject {{
                font-size: 1.5rem;
                font-family: 'Poppins', sans-serif;
                margin-bottom: 20px;
            }}
            .text {{
                font-size: 1rem;
                font-family: 'Poppins', sans-serif;
            }}
            #email, #otp {{
                font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <span class="logo">LearnSync</span>
            <span class="subject">{subject}</span>
            <div class="text">Your OTP for email <span id="email">{email}</span> is <span id="otp">{otp}</span>.</div>
        </div>
    </body>
    </html>
    """.format(subject=subject, email=email, otp=otp)

    # Create MIME message
    msg = MIMEMultipart()
    msg['From'] = 'taccovan001@gmail.com'
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_content, 'html'))

    # Connect to SMTP server and send email
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('taccovan001@gmail.com', 'zrntrzoqwjgdhjzs')  # Update with your email password
    server.sendmail(email, email, msg.as_string())
    server.quit()

    return jsonify({'otp': otp})

def createFlashCard(name, category, hashtags_list, flashcard_data, user_name):
    collection = db["flashcards"]

    new_flashcard_pack = {
        "name" : name,
        "category" : category,
        "hashtags" :hashtags_list,
        "created_by": user_name, 
        "created_at": datetime.utcnow().strftime('%Y-%m-%d'),
        "times_opened": 0,
        "flashcard_data": flashcard_data
    }
    insert_result = collection.insert_one(new_flashcard_pack)

    # Retrieve ObjectId of inserted document
    id = insert_result.inserted_id

    return id

# Supporting function for fetching specific flashcard
def fetch_flashcard_by_id(flashcard_id):
    collection = db["flashcards"]
    flashcard_object_id = ObjectId(flashcard_id)
    flashcard = collection.find_one({"_id": flashcard_object_id})

    # For updating frequence of opening
    times_opened = flashcard['times_opened'] + 1
    filter = {'_id': ObjectId(flashcard_id)}
    update = {'$set': {'times_opened': times_opened}}
    collection.update_one(filter, update)
    # print(times_opened)
    # print(type(flashcard))
    return flashcard

# Function to fetch object of user from its object_id
def fetch_user_by_id(user_id):
    collection = db["users"]
    user_object_id = ObjectId(user_id)
    user = collection.find_one({"_id": user_object_id})
    # print(type(user))
    return user

@app.route('/get-reqs-for-user', methods = ['POST'])
def get_requests_for_receiver():
    receiver_id = request.get_json()
    receiver_id = receiver_id.get('receiver_id')
    collection = db["requests"]
    receiver_object_id = ObjectId(receiver_id)
    receiver = fetch_user_by_id(receiver_object_id)
    # print(receiver, "It is receiver")
    requests = list(collection.find({"receiver": receiver['username'], "status": "pending"}))
    #  requests = list(collection.find({"receiver": receiver['username'], "status": "pending"}).sort([("timestamp_field", -1)]))
    # print(requests)
    for req in requests:
        req['_id'] = str(req['_id'])
    # print(jsonify(requests))
    return jsonify(requests)

@app.route('/get-noti-for-user', methods=['POST'])
def get_notification_for_receiver():
    receiver_id = request.get_json()
    receiver_id = receiver_id.get('receiver_id')
    collection = db["notifications"]
    receiver_object_id = ObjectId(receiver_id)
    receiver = fetch_user_by_id(receiver_object_id)
    notifications = list(collection.find({"receiver": receiver['username'], "status": "pending"}).sort("timestamp", -1))
    notifications.sort(key=lambda x: x['timestamp'], reverse=True)
    for req in notifications:
        req['_id'] = str(req['_id'])
    return jsonify(notifications)

def get_requests_sender_or_receiver(object_id):
    collection = db["requests"]
    object_id = ObjectId(object_id)
    requests = list(collection.find({"$or": [{"sender": object_id}, {"receiver": object_id}]}))
    return requests







# 
# Main Entry Point of Program 
# 
@app.route('/')
def index():
    return render_template('home_alt.html')





#
# Code for Login and Homepage
#

# Code to handle login request
@app.route('/login', methods=['GET', 'POST'])
def login():
    collection = db["users"]
    if request.method == 'POST':
        username = request.form.get('username')
        # print(username, password)
        user = collection.find_one({'username': username})
        session['username'] = user['username']
        session['user_id'] = str(user['_id'])
        # print(session.get('username'))
        # requests = get_requests_for_receiver(str(user['_id']))
        # print(requests)
        # print(user)
        # user_object = User(user['_id'])
        return render_template('dashboard.html', user=user)
    else:
        return render_template('home_alt.html')





# 
# Code For FlashCard Goes Here
# 
@app.route('/insert-flash-card/', methods=['POST'])
def insertFlashCard():
    data = []
    username = session.get('username')
    name = request.form['name']
    hashtags = request.form['tags']
    hashtags_list = [f"#{tag.strip()}" if not tag.startswith("#") else tag.strip() for tag in hashtags.split()]
    subject = request.form['subject']
    questions = request.form.getlist('question[]')
    answers = request.form.getlist('answer[]')
    
    for i in range(len(min(questions,answers))):
        data.append((questions[i], answers[i]))

    flashcard_id = createFlashCard(name, subject, hashtags_list, data, username)
    if flashcard_id:
        return jsonify({'message': 'Flashcard created successfully', 'flashcard_id': str(flashcard_id)}), 200
    else:
        return jsonify({'message': 'Failed to create flashcard'}), 500



#
# User Signup Stuff
#

# Function to Handle Signup
import sendMail
@app.route('/sign-up', methods=['POST','GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        user = createUser(username, password, email)

        collection = db["users"]
        user = collection.find_one({'username': username})
        session['username'] = user['username']
        session['user_id'] = str(user['_id'])
        # user_id = str(user.inserted_id)
        # user = fetch_user_by_id(user_id)
        # print(user)
        user = collection.find_one({'username': username})
        return render_template('dashboard.html', user=user)
        return render_template('home_alt.html')
    else:
        return render_template('signup.html')





#
# All code stuff for Flashcards goes here
#

# Main windows of FlashCard section of app
@app.route('/flash_card/<user_id>',methods=['GET'])
def flashCardApp(user_id):
    categories = ["Literature", "Mathematics", "Science", "History", "Geography", "Computer Science", "Art", "Music", "Health", "Business", "Test Preparation", "Miscellaneous"]

    collection = db["flashcards"]
    flashcards_cursor = collection.find({})
    flashcards = list(flashcards_cursor)
    # print(flashcards)
    for flashcard in flashcards:
        flashcard['_id'] = str(flashcard['_id'])

    # print(flashcards)
    base_url = request.url_root
    return render_template('flash_cards.html', user_id = user_id, flashcards=flashcards, base_url=base_url)

# Function for opening a particular flashcard
@app.route('/flashcard/<flashcard_id>')
def view_flashcard(flashcard_id):
    flashcard = fetch_flashcard_by_id(flashcard_id)
    return render_template('view_flashcard.html', flashcard=flashcard)

@app.route('/fetch-all-flashcards', methods=['POST'])
def fetchall_flashcards():
    collection = db["flashcards"]
    flashcards_cursor = collection.find({}).sort("created_at", -1)
    flashcards = list(flashcards_cursor)
    # print(flashcards)
    for flashcard in flashcards:
        flashcard['_id'] = str(flashcard['_id'])

    return jsonify(flashcards)

@app.route('/fetch-user-flashcards/<user_id>', methods=['POST'])
def fetchUserFlashcards(user_id):
    # user_id = request.json.get('user_id')
    collection = db["flashcards"]
    user = fetch_user_by_id(user_id)
    user_name = user['username']
    # Search for the keyword in the name or category fields using a case-insensitive regular expression
    query = {
        "created_by": {"$regex": user_name, "$options": "i"}
    }
    # Fetch all flashcards that match the query
    cursor = collection.find(query).sort("created_at", -1)
    # Convert ObjectId to string and format the results
    flashcards = [flashcard for flashcard in cursor]
    for flashcard in flashcards:
        flashcard['_id'] = str(flashcard['_id'])
    # print(flashcards)
    return jsonify(flashcards)

@app.route('/search-user-flashcards', methods=['POST'])
def searchUserFlashcards():
    keyword = request.json.get('keyword')
    collection = db["flashcards"]
    username = session.get('username')
    # Search for the keyword in the name or category fields using a case-insensitive regular expression
    query = {
        "$and": [
            {"$or": [
                {"name": {"$regex": keyword, "$options": "i"}},
                {"category": {"$regex": keyword, "$options": "i"}},
                {"flashcard_data": {"$elemMatch": {"$elemMatch": {"$regex": keyword, "$options": "i"}}}},
                {"hashtags": {"$regex": keyword, "$options": "i"}}
            ]}, 
        {"created_by": username}
        ]
    }
    # Fetch all flashcards that match the query
    cursor = collection.find(query).sort("created_at", -1)
    # Convert ObjectId to string and format the results
    flashcards = [flashcard for flashcard in cursor]
    for flashcard in flashcards:
        flashcard['_id'] = str(flashcard['_id'])
    return jsonify(flashcards)

@app.route('/search-flashcards', methods=['POST'])
def searchFlashcards():
    keyword = request.json.get('keyword')
    collection = db["flashcards"]
    username = session.get('username')
    # Search for the keyword in the name or category fields using a case-insensitive regular expression
    query = {
        "$or": [
                {"name": {"$regex": keyword, "$options": "i"}},
                {"category": {"$regex": keyword, "$options": "i"}},
                {"flashcard_data": {"$elemMatch": {"$elemMatch": {"$regex": keyword, "$options": "i"}}}},
                {"hashtags": {"$regex": keyword, "$options": "i"}}
            ]
    }
    # Fetch all flashcards that match the query
    cursor = collection.find(query).sort("created_at", -1)
    # Convert ObjectId to string and format the results
    flashcards = [flashcard for flashcard in cursor]
    for flashcard in flashcards:
        flashcard['_id'] = str(flashcard['_id'])
    return jsonify(flashcards)


#
# Friends Functionality Goes Here...
# 

# Function for add friend fuctionality
@app.route("/add-friend", methods=['POST'])
def addFriend():
    user_id = session.get('user_id')
    user = fetch_user_by_id(user_id)
    friend_username = request.form['friend-username']
    # print(friend_username)
    # print(user['username'] + "Is the user name")
    # result = db["users"].update_one({"_id": ObjectId(user_id)}, {"$push": {"friends": friend_username}})
    # print(result)
    if friend_username in user['friends']:
        return jsonify({'message': 'Friend already in friends list'}), 400
    else:
        # If not, add the friend to the user's friends array
        # result = db["users"].update_one({"_id": ObjectId(user_id)}, {"$push": {"friends": friend_username}})
        if createRequest(user['username'], friend_username, 0):
            return jsonify({'message': 'Friend Request Sent!'}), 200
        else:
            return jsonify({'message': 'Failed to add friend'}), 500

def handleFriendSearch():
    user_id = session.get('user_id')
    user = fetch_user_by_id(user_id)
    friend_username = request.form['friend-username']
    if friend_username in user['friends']:
        return jsonify({'message': 0}), 400
    else:
        # If not, add the friend to the user's friends array
        # result = db["users"].update_one({"_id": ObjectId(user_id)}, {"$push": {"friends": friend_username}})
        if createRequest(user['username'], friend_username, 0):
            return jsonify({'message': 'Friend Request Sent!'}), 200
        else:
            return jsonify({'message': 'Failed to add friend'}), 500

# Function to accept friend request
@app.route("/accept-friend-request/<request_id>", methods=['POST'])
def accept_friend_request(request_id):
    # Assuming you have a requests collection in your database
    collection = db["requests"]
    # Find the request by its ObjectId
    request_object_id = ObjectId(request_id)
    request_doc = collection.find_one({"_id": request_object_id})
    # Assuming you have a users collection in your database
    users_collection = db["users"]
    
    if request_doc:
        sender_username = request_doc['sender']
        receiver_username = request_doc['receiver']
        
        # Update sender's friend list
        users_collection.update_one({"username": sender_username}, {"$push": {"friends": receiver_username}})
        # Update receiver's friend list
        users_collection.update_one({"username": receiver_username}, {"$push": {"friends": sender_username}})
        
        # Change the status of the request to accepted
        collection.update_one({"_id": request_object_id}, {"$set": {"status": "accepted"}})
        
        return jsonify({'message': 'Friend request accepted successfully'}), 200
    else:
        return jsonify({'message': 'Friend request not found'}), 404
    
# Function to reject friend request
@app.route("/reject-friend-request/<request_id>", methods=['POST'])
def reject_friend_request(request_id):
    collection = db["requests"]
    request_object_id = ObjectId(request_id)
    # Update the status of the request to rejected
    collection.update_one({"_id": request_object_id}, {"$set": {"status": "rejected"}})
    return jsonify({'message': 'Friend request rejected successfully'}), 200

@app.route("/close-notification/<notification_id>", methods=['POST'])
def closeNotification(notification_id):
    # Assuming you have a requests collection in your database
    collection = db["notifications"]
    # Find the request by its ObjectId
    notification_object_id = ObjectId(notification_id)
    notification_doc = collection.find_one({"_id": notification_object_id})
    # Assuming you have a users collection in your database
    # print(notification_doc)
    users_collection = db["users"]
    
    if notification_doc:
        # Change the status of the notification to accepted
        collection.update_one({"_id": notification_object_id}, {"$set": {"status": "viewed"}})
        
        return jsonify({'message': 'Notification closed successfully'}), 200
    # else:
    #     return jsonify({'message': 'Notification not found'}), 404

# Function to send a removal request to a friend
@app.route("/remove-friend/<username>", methods=['POST'])
def removeFriend(username):
    try:
        # Assuming you have a users collection in your database
        users_collection = db["users"]
        
        # Get the current user's username from the session or token
        # For demonstration purposes, I'll assume the username is stored in a variable called current_username
        current_username = session.get('username')
        
        # Remove the friend from the current user's friend list
        users_collection.update_one({"username": current_username}, {"$pull": {"friends": username}})
        
        # Remove the current user from the friend's friend list
        users_collection.update_one({"username": username}, {"$pull": {"friends": current_username}})
        
        createNotification(current_username, username, 2)

        return jsonify({'message': 'Friend removed successfully'}), 200
    except Exception as e:
        return jsonify({'message': f'Failed to remove friend: {str(e)}'}), 500

@app.route('/update-daily-task', methods=['POST'])
def update_daily_tasks():
    collection = db['users']
    if request.method == 'POST':
        username = session.get('username')
        if username:
            task_list = request.form.get('task')
            updated_tasks = {'task': task_list, 'priority': 2, 'completed': 0, 'lastupdate': datetime.utcnow()} 
            collection.update_one({'username': username}, {'$push': {'dailytasks': {'$each': updated_tasks}}})
            return jsonify({'message': 'Tasks updated successfully'}), 200
        else:
            return jsonify({'message': 'Username not provided in the form data'}), 400
    else:
        return jsonify({'message': 'Method not allowed'}), 405

# Function for sharing user stats with homepage
def fetch_user_stats(user_id):
    # Connect to MongoDB

    # Query the users collection to get the user's stats
    users_collection = db["users"]
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    # print(user)
    # Check if the user exists
    if user:
        # Extract and return the user stats
        user_stats = user.get("stats", {})
        # print(user_stats)
        return user_stats
    else:
        # Return None if the user is not found
        return None

@app.route('/getUserStats', methods=['POST'])
def getUserStats():
    userId = session.get('user_id')
    # print(userId)
    # print(request)
    # user_id = request.form.get('userId')
    user_id = userId
    user_stats = fetch_user_stats(user_id)
    # print(user_stats, "user stats")
    # print(user_id,"Turueueddkdkdkdkue")
    return jsonify(user_stats)

@app.route('/getUser/<userId>', methods = ['POST'])
def getUser(userId):
    request_data = request.get_json()
    # user_id = request_data.get('userId')
    # print(request_data)
    user = db.users.find_one({"_id" : ObjectId(userId)})
    user_data = {
    '_id': str(user['_id']),
    'username': user['username'],
    'password': 'protected',
    'stats': [{'streaks': user['stats'][0]['streaks'], 'gems': user['stats'][0]['gems'], 'hearts': user['stats'][0]['hearts']}],
    'groups': user['groups'],
    'friends': user['friends'],
    'pomodoro_sequences': user['pomodoro_sequences']
    }

    user['_id'] = str(user['_id'])
    # print((user_data))
    # return user
    # print(user)
    user['password'] = user['password'].decode('utf-8')
    return jsonify(user)


#
#
# Pomodoro Timer Code Goes Here
#
#
@app.route('/update-user-sequences', methods=['POST'])
def update_sequences():
    # Get the updated sequences data from the request
    sequences = request.form.getlist('sequence[]')
    # print(sequences,"Mear wala sequences hai yeh!")
    
    # Remove empty or zero-length arrays from sequences
    sequences = [[float(num) for num in seq.split(',')] for seq in sequences if seq.strip()]

    # Assuming you have a collection named 'users' in your database
    collection = db["users"]

    # Get the current user's ID from the session
    user_id = session.get('user_id')

    # Update the sequences data for the current user in the database
    result = collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"pomodoro_sequences": sequences}}
    )

    if result.modified_count == 1:
        return jsonify({'message': 'Sequences updated successfully'}), 200
    else:
        return jsonify({'message': 'No documents were modified. User not found or sequences unchanged.'}), 404

#
#
#   Everything for groups goes here
#
#

@app.route('/check-groupname-availability', methods=['POST'])
def checkGroupnameAvailability():
    collection = db["groups"]
    groupname = request.form.get('groupname')
    # print(groupname)
    group = collection.find_one({'name': groupname})
    if group:
        # print("Group name already exists.")
        return jsonify({'message': 'Groupname is not available'}), 409
    else:
        # print("Group name is available.")
        return jsonify({'message': 'Groupname available'}), 200

@app.route('/check-groupname-availability', methods=['POST'])
def check_groupname_available():
    collection = db["groups"]
    name = request.form.get('name')
    user = collection.find_one({'name': name})
    if user:
        return jsonify({'message': 'Username already exists'}), 409
    else:
        return jsonify({'message': 'Username available'}), 200
    
@app.route('/update-daily-task', methods=['POST'])
def update_daily_task():
    collection = db["users"]
    try:
        # Retrieve user ID from session or request data
        #_id = session.get('_id')  # Assuming user ID is stored in the session
        _id = request.form.get('_id')  # Assuming user ID is sent in the request data

        # Retrieve task data from request parameters
        tasks_data = request.form.getlist('task[]')

        # Check if tasks data is provided
        if not tasks_data:
            return jsonify({'success': False, 'error': 'No tasks provided'}), 400

        # Construct list of task objects
        tasks = [{
            'task': task,
            'priority': 1,
            'completed': False,
            'lastupdate': datetime.utcnow()
        } for task in tasks_data]

        # Update user's dailytasks array with new tasks
        result = collection.update_one({'_id': ObjectId(_id)}, {'$push': {'dailytasks': {'$each': tasks}}}, upsert=True)

        # Check if tasks were successfully added
        if result.modified_count > 0 or result.upserted_id is not None:
            return jsonify({'success': True, 'message': 'Tasks added successfully'}), 200
        else:
            return jsonify({'success': False, 'error': 'Failed to add tasks'}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': f'An error occurred: {str(e)}'}), 500


@app.route('/create-group', methods=['POST'])
def insertNewGroup():
    # print(request.form)
    groupname = request.form.get('groupname')
    selected_friends = request.form.get('selectedFriends')
    selected_friends = json.loads(selected_friends)
    # print(selected_friends)

    user = session.get('username')
    # print(user)
    group_id = createGroup(groupname, user, selected_friends, datetime.now())

    if group_id:
        return jsonify({'message': 'Group created successfully', 'group_id': str(group_id)}), 200
    else:
        return jsonify({'message': 'Failed to create group'}), 500
    
@app.route('/get-user-groups/<mode>', methods=['POST'])
def getUserGroups(mode):
    try:
        # Get the username from the session
        username = session.get('username')
        
        # Get the query from the form data
        query = request.form.get('query')

        # Access the groups collection
        groups_collection = db["groups"]

        # Determine the filter based on the mode
        filter_query = {"members": username} if int(mode) == 2 else {"group_leader": username}

        # Fetch user groups based on the filter
        if query:  # If query is not empty, filter groups based on the query
            user_groups = list(groups_collection.find({**filter_query, "name": {"$regex": query, "$options": "i"}}))
        else:  # If query is empty, fetch all groups based on the filter
            user_groups = list(groups_collection.find(filter_query))

        # Convert ObjectId to string for JSON serialization
        for group in user_groups:
            group['_id'] = str(group['_id'])

        # Return the response
        return jsonify([username, user_groups])

    except Exception as e:
        # Handle any errors that occur during the process
        return jsonify({'error': str(e)}), 500    

@app.route("/get-friends-list", methods=["POST"])
def getUserFriends():
    try:
        collection = db["users"]
        
        user_object_id = ObjectId(session.get('user_id'))
        user = collection.find_one({"_id": user_object_id})
        
        if user:
            friends = user.get("friends", [])
            
            return friends
        else:
            return None
    except Exception as e:
        # print(f'An error occurred: {str(e)}')
        return None


def createTask(group_Id, group_name, task_name, task_completion_date, group_members):
    try:
        # Connect to the tasks collection in the database
        tasks_collection = db["tasks"]
        
        # Create a new task document
        new_task = {
            "group_id": group_Id,
            "group_name": group_name,
            "task_name": task_name,
            "task_completion_date": task_completion_date,
            "creation_date": datetime.now(),
            "members_status": {member: "pending" for member in group_members},
            "task_status":"incomplete"
        }
        
        result = tasks_collection.insert_one(new_task)
        
        if result.inserted_id:
            return True, result.inserted_id
        else:
            return False, None
    except Exception as e:
        return False, None


@app.route('/create-group-task', methods=['POST'])
def create_group_task():
    try:
        # Extract data from the request
        group_id = request.form.get('group_Id')
        group_name = request.form.get('group_name')
        task_name = request.form.get('task_name')
        task_completion_date = request.form.get('task_completion_date')
        
        # Fetch the members of the group
        group_members = getGroupMembers(group_id)
        
        # Call the createTask function to insert the task into the database
        success, task_id = createTask(ObjectId(group_id), group_name, task_name, task_completion_date, group_members)
        
        if success:
            for member in group_members:
                createNotification(group_name, member, 5)  # Notify each member about the new task
            return jsonify({'message': 'Task created successfully'}), 200
        else:
            return jsonify({'message': 'Failed to create task'}), 500
    except Exception as e:
        return jsonify({'message': f'An error occurred: {str(e)}'}), 500

def changeTaskStatus(task_id, member_name, new_status):
    try:
        # Connect to the tasks collection in the database
        tasks_collection = db["tasks"]
        
        # Find the task by its ObjectId
        task_object_id = ObjectId(task_id)
        task = tasks_collection.find_one({"_id": task_object_id})
        
        # Update the status of the specified member for the task
        task["members_status"][member_name] = new_status
        
        # Update the task document in the database
        result = tasks_collection.update_one({"_id": task_object_id}, {"$set": {"members_status": task["members_status"]}})
        
        if result.modified_count == 1:
            return True
        else:
            return False
    except Exception as e:
        return False
from pymongo.errors import PyMongoError
@app.route('/remove-grp-member', methods=['POST'])
def removeMemberFromGroup():
    try:
        # Get data from request
        group_id = request.json.get('group_id')
        member_name = request.json.get('member_name')
        print(group_id, member_name)

        # Check if group exists
        groups_collection = db["groups"]
        group = groups_collection.find_one({"_id": ObjectId(group_id)})
        if not group:
            return jsonify({'message': 'Group not found'}), 404

        # Update group document to remove the member from 'members' list
        result = groups_collection.update_one(
            {"_id": ObjectId(group_id)},
            {"$pull": {"members": member_name}}
        )

        # Check if group document was updated successfully
        if result.modified_count > 0:
            # Update tasks to remove the member from 'members_status' dictionary
            tasks_collection = db["tasks"]
            tasks_collection.update_many(
                {"group_id": ObjectId(group_id)},
                {"$unset": {"members_status." + member_name: ""}}
            )

            users_collection = db["users"]
            users_collection.update_many(
                {"username": member_name},  # Assuming member_name is the username of the user
                {"$pull": {"groups": group["name"]}}  # Remove group name from groups array
            )

            return jsonify({'message': 'Removed successfully from group and tasks'}), 200
        else:
            return jsonify({'message': 'Failed to remove group member'}), 500

    except PyMongoError as e:
        return jsonify({'error': str(e)}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get-grp-members', methods=['POST'])
def getGrpMembers():
    group_id = request.json.get('group_id')
    groups_collection = db["groups"]
    group = groups_collection.find_one({"_id": ObjectId(group_id)})
    if group:
        arr = group.get('members', [])
        return jsonify(arr), 200
    else:
        return jsonify({'message': 'Failed to fetch group members'}), 500

def getGroupMembers(group_id):
    # Assuming you have a groups collection in your database
    groups_collection = db["groups"]
    group = groups_collection.find_one({"_id": ObjectId(group_id)})
    if group:
        return group.get('members', [])
    else:
        return []

@app.route('/get-group-tasks', methods=['POST'])
def get_group_tasks():
    try:
        group_id = request.json.get('group_id')
        # print(group_id)
        tasks_collection = db["tasks"]
        current_date = datetime.now()
        group_tasks = list(tasks_collection.find({"group_id": ObjectId(group_id)}).sort("task_completion_date", 1))
        
        # print(group_tasks)
        print(group_tasks)
        # Convert task_completion_date strings to datetime objects
        for task in group_tasks:
            task["task_completion_date"] = datetime.strptime(task["task_completion_date"], "%Y-%m-%d")
        
        # closest_tasks = [task for task in group_tasks if task["task_completion_date"] >= current_date]
        
        closest_tasks = group_tasks

        for task in closest_tasks:
            task['_id'] = str(task['_id'])
            task['group_id'] = str(task['group_id'])
            # print(task)
        print(closest_tasks)
        arr = [session.get('username'), closest_tasks];
        return jsonify(arr), 200
    except Exception as e:
        print(f'An error occurred: {str(e)}')
        return jsonify({'message': 'Failed to fetch tasks for the group'}), 500

@app.route('/delete-group-task', methods=['POST'])
def deleteGroupTask():
    try:
        # Extract the task ID from the request
        task_id = request.json.get('task_id')
        
        # Assuming you have a tasks collection in your database
        tasks_collection = db["tasks"]
        
        # Delete the task document from the database using its ID
        result = tasks_collection.delete_one({"_id": ObjectId(task_id)})
        
        if result.deleted_count == 1:
            # Task deletion successful
            return jsonify({'success': True, 'message': 'Task deleted successfully'}), 200
        else:
            # Task not found or deletion unsuccessful
            return jsonify({'success': False, 'message': 'Task not found or deletion unsuccessful'}), 404
    except Exception as e:
        # Handle any errors that occur during the deletion process
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500

@app.route('/delete-group', methods=['POST'])
def deleteGroup():
    try:
        # Extract the group ID from the request
        group_id = request.json.get('groupId')
        
        # Assuming you have a groups collection in your database
        groups_collection = db["groups"]
        
        # Find the group document from the database using its ID
        group = groups_collection.find_one({"_id": ObjectId(group_id)})
        
        if not group:
            return jsonify({'success': False, 'message': 'Group not found'}), 404
        
        # Store group name
        group_name = group.get('name')
        
        # Delete the group document from the database using its ID
        result = groups_collection.delete_one({"_id": ObjectId(group_id)})
        
        if result.deleted_count == 1:
            # Group deletion successful, remove group from users' groups arrays
            users_collection = db["users"]
            
            # Iterate through members of the group and remove group from their groups arrays
            members = group.get('members', [])
            users_collection.update_many(
                {"username": {"$in": members}},
                {"$pull": {"groups": group_name}}
            )
            
            tasks_collection = db["tasks"]
            tasks_collection.delete_many({"group_id": ObjectId(group_id)})

            for member in members:
                createNotification(session.get('username'), member, 6, group_name)

            return jsonify({'success': True, 'message': 'Group deleted successfully and removed from users'}), 200
        else:
            # Group not found or deletion unsuccessful
            return jsonify({'success': False, 'message': 'Group not found or deletion unsuccessful'}), 404
    except Exception as e:
        # Handle any errors that occur during the deletion process
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500

@app.route('/mark-my-task', methods=['POST'])
def markMyTaskAsComplete():
    try:
        # Extract the task ID from the request
        task_id = request.json.get('task_id')
        mode = request.json.get('mode')
        for_user = request.json.get('user')
        
        tasks_collection = db["tasks"]
        
        # Find the task document from the database using its ID
        task = tasks_collection.find_one({"_id": ObjectId(task_id)})
        print(task['members_status'][for_user])
        if task:
            # Update the status of the specified user in the members_status array
            task['members_status'][for_user] = mode
            
            # Update the task document in the database
            result = tasks_collection.update_one({"_id": ObjectId(task_id)}, {"$set": task})
            
            if result.modified_count == 1:
                # Task status updated successfully
                return jsonify({'success': True, 'message': 'Task status updated successfully'}), 200
            else:
                # Task not found or update unsuccessful
                return jsonify({'success': False, 'message': 'Task not found or update unsuccessful'}), 404
        else:
            # Task not found
            return jsonify({'success': False, 'message': 'Task not found'}), 404
    except Exception as e:
        # Handle any errors that occur during the update process
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500
    
@app.route('/fetch_random_riddle', methods=['GET'])
def fetch_random_riddle():
    # Connect to MongoDB
    collection = db["riddles"]

    # Fetch total number of riddles
    total_riddles = collection.count_documents({})

    # Generate a random number within the range of total riddles
    random_index = random.randint(0, total_riddles - 1)

    # Fetch the random riddle from MongoDB
    random_riddle = collection.find({}, {'_id': 0}).skip(random_index).limit(1)[0]
    return jsonify(random_riddle)

# 
# Main() function of app
# 
if __name__ == '__main__':
    app.run(debug=True, port=8888)
