from datetime import datetime, timedelta
import os
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
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
import tensorflow as tf
import matplotlib.pyplot as plt

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time

app = Flask(__name__)

app.secret_key = secrets.token_hex(24)

def suggest_pomodoro_sequence(user_usage_hours, collection, tolerance=5):
    # Filter data based on user's total usage hours with tolerance

    close_entries = collection.find({
        'Total Usage Hours': {'$gte': user_usage_hours - tolerance, '$lte': user_usage_hours + tolerance}
    })

    # Convert MongoDB cursor to DataFrame
    close_data = pd.DataFrame(list(close_entries))

    # If no close entries found, return None
    if len(close_data) == 0:
        return None

    # Group by sequence and calculate average rating for each sequence
    sequence_ratings = close_data.groupby('Pomodoro Sequence')['Rating'].mean().reset_index()

    # Sort sequences based on average rating
    sorted_sequences = sequence_ratings.sort_values(by='Rating', ascending=False)

    # If no sequences found, return None
    if len(sorted_sequences) == 0:
        return None

    # Select the top rated sequence
    top_sequence = sorted_sequences.iloc[0]['Pomodoro Sequence']

    # Calculate average sequence
    average_sequence = [int(x) for x in top_sequence.split(',')]

    return average_sequence

def build_model(input_shape):
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(input_shape,)),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    return model

def train_model(model, X_train, y_train, epochs=50, batch_size=32):
    model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=0)

@app.route('/get-ai-suggestion')
def getAISuggestion():
    suggested_sequence = suggest_pomodoro_sequence(session.get('total_usage_hours'), db['suggestions_data'], tolerance=5)
    sleeps = [3,7,5,4,6]
    time.sleep(random.choice(sleeps))
    if suggested_sequence:
        return jsonify({'suggested_sequence': suggested_sequence})
    else:
        return jsonify({'error': 'No suitable sequence found within the specified tolerance'})

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
                "hearts":0,                
            }
        ], 
        "groups": [],
        "friends": [],
        "streaks_with": [],
        "daily_tasks_data": [
            {"lastComplete" : 0,
             "daysCompletes":[],
             "longestStreak": 0,
             "userRank":0,
             "userScore":0,
             "experience":"rookie",
             "highestRank":10000
            }
        ],
        "todays_task":{'complete':0, 'total':0},
        "task_stat":[],
        "todays_pomo":0,
        "pomodoro_stat" : [],
        "consecutive_login":0,
        "last_login":datetime.now(),
        "pomodoro_sequences":[
            [25.0,5.0,25.0,5.0,25.0,30.0],
            [60.0,10.0,60.0,10.0,60.0,30.0],
            [75.0,15.0,45.0,10.0,30.0,60.0]
        ], "joinging_date" : datetime.now(),
        "pomodoro_usage_hours" : 0.0
    }

    new_user = collection.insert_one(new_user)
    return new_user

@app.route('/add-time-to-user', methods=['POST'])
def add_time_to_user():
    # Get the data from the request
    data = request.json

    # Extract the variable value
    variable = data['variable']
    """

    """
    # Assuming you have a function to find and update the user in the database
    # Here's a sample implementation
    username = session.get('username')
    user = db.users.find_one({"username": username})
    if user:
        # Update the user's pomodoro_usage_hours
        user['pomodoro_usage_hours'] += variable
        user['todays_pomo'] += variable
        # Update the user's joining_date if needed
        # Assuming you have a function to update the user in the database
        db.users.update_one({"username": username}, {"$set": user})
        return jsonify({"message": "User's time & daily time updated successfully"})
    else:
        return jsonify({"error": "User not found"})

def createDailyTask(task_name, task_priority):
    # Select the collection
    collection = db["dailys"]

    # Create a new task document
    new_task = {
        "createdBy": ObjectId(session.get('user_id')),
        "creationDate": datetime.now(),
        "task_name": task_name,
        "priority": task_priority,
        "completed": 0,  # Assuming 0 means task is not completed, adjust as needed
        "lastCompleted": datetime(1900, 1, 1)  # Assuming initial value for lastCompleted, adjust as needed
    }

    try:
        # Insert the new task document into the collection
        result = collection.insert_one(new_task)
        print("New task created with ID:", result.inserted_id)
        return result.inserted_id  # Return the ID of the newly inserted document
    except Exception as e:
        print("Error creating task:", e)
        return None

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
        3:'Streak Started!',
        8:'Sent Daily Streak',
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
    try:
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

    except Exception as e:
        # If an exception occurs, return an error response
        return jsonify({'error': str(e)})

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

def update_todays_task(user_id):
    # Assuming db is the MongoDB database connection
    dailys_collection = db['dailys']
    users_collection = db['users']
    
    # Find tasks created by the user
    user_tasks = dailys_collection.find({"createdBy": ObjectId(user_id)})
    
    # Count the total and completed tasks
    total_tasks = dailys_collection.count_documents({"createdBy": ObjectId(user_id)})
    completed_tasks = dailys_collection.count_documents({"createdBy": ObjectId(user_id), "completed": 1})
    
    # Update the user document with today's task data
    users_collection.update_one({"_id": ObjectId(user_id)}, {
        "$set": {
            "todays_task": {"complete": completed_tasks, "total": total_tasks}
        }
    })

# Code to handle login request
@app.route('/login', methods=['GET', 'POST'])
def login():
    collection = db["users"]
    if request.method == 'POST':
        username = request.form.get('username')
        user = collection.find_one({'username': username})
        session['username'] = user['username']
        session['user_id'] = str(user['_id'])
        session['total_usage_hours'] = int(user['pomodoro_usage_hours'])
        # user['none']
        update_todays_task(str(user['_id']))

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

@app.route('/sign-up', methods=['GET'])
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
        # # user_id = str(user.inserted_id)
        # # user = fetch_user_by_id(user_id)
        # # print(user)
        user = collection.find_one({'username': username})
        session['total_usage_hours'] = int(user['pomodoro_usage_hours'])
        # return render_template('dashboard.html', user=user)
        # print("I am Called")
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
    print(user_id)
    user = fetch_user_by_id(user_id)
    print(user)
    friend_username = request.form['friend-username']
    print(friend_username)
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
@app.route("/remove-friend", methods=['POST'])
def removeFriend():
    try:
        friend_username = request.form.get('friend_username')
        
        # Assuming you have a users collection in your database
        users_collection = db["users"]
        
        # Get the current user's username from the session or token
        # For demonstration purposes, I'll assume the username is stored in a variable called current_username
        current_username = session.get('username')
        
        # Remove the friend from the current user's friend list
        users_collection.update_one({"username": current_username}, {"$pull": {"friends": friend_username}})
        
        # Remove the current user from the friend's friend list
        users_collection.update_one({"username": friend_username}, {"$pull": {"friends": current_username}})
        
        createNotification(current_username, friend_username, 2)

        return jsonify({'message': 'Friend removed successfully'}), 200
    except Exception as e:
        return jsonify({'message': f'Failed to remove friend: {str(e)}'}), 500

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

def getUserByUsername(username):
    collection = db["users"]
    
    # Query the user by username
    user = collection.find_one({"username": username})
    
    # If user is found, remove _id and password fields
    if user:
        del user["_id"]
        del user["password"]
        del user["pomodoro_sequences"]
        return user
    else:
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
    # request_data = request.get_json()
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

@app.route('/get-user-friends/<mode>', methods=['POST'])
def getUserFriends1(mode):
    try:
        # Get the username from the session
        userId = session.get('user_id')
        user = db.users.find_one({"_id" : ObjectId(userId)})
        # print(user.json()('friends'))
        friend_list = user['friends']
        
        # Get the query from the form data
        query = request.form.get('query')
        if query:  # If query is not empty
            matching_friends = [friend for friend in friend_list if query.lower() in friend.lower()]
            return jsonify(matching_friends)
        else:  # If query is empty
            return jsonify(friend_list)

    except Exception as e:
        print(e)
        # Handle any errors that occur during the process
        return jsonify({'error': str(e)}), 500    

@app.route('/get-friend-details', methods=['POST'])
def getFriendDetails():
    try:
        friend_name = request.form.get('friend')
        print(friend_name + " This is friend name")
        userId = session.get('user_id')
        collection = db['users']
        user = collection.find_one({"_id" : ObjectId(userId)})  # Assuming you have a MongoDB database connection called 'db'
        friend = getUserByUsername(friend_name)
        print(friend)

        user1_friends = list(user.get("friends", []))  # Convert to list
        user2_friends = list(friend.get("friends", []))  # Convert to list
        common_friends = len(set(user1_friends).intersection(user2_friends))  # Find intersection after converting to set

        user1_groups = list(user.get("groups", []))  # Convert to list
        user2_groups = list(friend.get("groups", []))  # Convert to list
        common_groups = len(set(user1_groups).intersection(user2_groups))  # Find intersection after converting to set

        data = {
            "friend": friend,
            "common_friends": common_friends,
            "common_groups": common_groups,
            "username": session.get('username')
        }
        print(data)
        return jsonify(data)
    except Exception as e:
        print(str(e) + " This is error")
        return jsonify({"error": str(e)}), 500



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


@app.route('/create-user-daily-task', methods=['POST'])
def createUserDailyTask():
    try:
        data = request.json
        input_value = data.get('value')
        input_level = int(data.get('level'))
        # Process the data (for demonstration, simply return it)
        task_id = str(createDailyTask(input_value, input_level))  # Call createDailyTask function and capture the returned ID
        print(task_id)
        return jsonify({
            'id': task_id,  # Include the ID in the response
            'value': input_value,
            'level': input_level,
            'message': 'Task created successfully'
        })
    
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

@app.route('/fetch-user-daily-tasks', methods=['GET'])
def fetchUserDailyTasks():
    try:
        # Select the collection
        collection = db["dailys"]
        
        # Fetch user's daily tasks
        user_id = ObjectId(session.get('user_id'))
        tasks = list(collection.find({"createdBy": user_id}))
        
        # Format tasks for response
        formatted_tasks = []
        for task in tasks:
            formatted_task = {
                'taskId': str(task['_id']),
                'taskName': task['task_name'],
                'taskPriority': task['priority'],
                'completed': task['completed']
            }
            formatted_tasks.append(formatted_task)
        
        # Return tasks as JSON response
        return jsonify(formatted_tasks)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/fetch-user-daily-tasks-to-show', methods=['GET'])
def fetchUserDailyTasksToShow():
    try:
        # Select the collection
        collection = db["dailys"]
        
        # Fetch user's daily tasks
        user_id = ObjectId(session.get('user_id'))
        tasks = list(collection.find({"createdBy": user_id}))
    
        all_tasks_completed = all(task.get('completed', 0) == 1 for task in collection.find({'createdBy': user_id}))
        
        # Format tasks for response
        formatted_tasks = []
        for task in tasks:
            formatted_task = {
                'taskId': str(task['_id']),
                'taskName': task['task_name'],
                'taskPriority': task['priority'],
                'completed': task['completed']
            }
            formatted_tasks.append(formatted_task)
        
        # Return tasks as JSON response
        return jsonify(formatted_tasks, all_tasks_completed)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update-user-daily-task', methods=['POST'])
def updateUserDailyTask():
    try:
        collection = db['dailys']
        data = request.json
        task_name = data.get('value')
        task_priority = data.get('level')
        task_id = data.get('id')

        collection.update_one(
            {'_id': ObjectId(task_id)},
            {'$set': {'task_name': task_name, 'priority': task_priority}}
        )
        
        response = {'message': 'Task updated successfully'}
        
        return jsonify(response), 200
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

@app.route('/delete-user-daily-task', methods=['POST'])
def deleteUserDailyTask():
    try:
        collection = db['dailys']
        data = request.json
        task_id = data.get('id')
        
        collection.delete_one({'_id': ObjectId(task_id)})
        
        response = {'message': 'Task deleted successfully'}
        
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/mark-daily-task-as-complete', methods=['POST'])
def mark_task_as_complete():
    try:
        # Get the task ID from the request data
        data = request.json
        task_id = data.get('taskId')
        mode = data.get('mode')
        
        collection = db['dailys']
        # Search for the task in the database
        task = collection.find_one({'_id': ObjectId(task_id)})
        # print(task)
        # Check if the task was found
        if task:
            # Toggle the completed status
            completed_status = 1 if task.get('completed', 0) == 0 else 0

            # Update the task's completed status
            today_date = datetime.now()
            updated_task = collection.find_one_and_update(
                {'_id': ObjectId(task_id)},
                {'$set': {'completed': completed_status, 'lastCompleted': today_date}},
                # return_document=True
            )
            user_id = ObjectId(session.get('user_id'))
            if updated_task:
                all_tasks_completed = all(task.get('completed', 0) == 1 for task in collection.find({'createdBy': user_id}))
                print(all_tasks_completed)
                if mode == 1:
                    collection = db['users']
                    user = collection.find_one({'_id': user_id})
                    user['daily_tasks_data'][0]['lastComplete'] = datetime.now()
                    user['daily_tasks_data'][0]['totalCompletes'].append(datetime.now())
                    user['stats'][0]['hearts'] += 1
                    collection.update_one({'_id': user['_id']}, {'$set': user})

                    if user['stats'][0]['hearts'] % 10 == 0:
                        if user['stats'][0]['hearts'] % 100 == 0:
                            user['stats'][0]['gems'] += user['stats'][0]['hearts'] // 100
                            # print(user['stats'][0]['hearts'] // 100)
                            # print(user['stats'][0]['gems'])
                        else:
                            user['stats'][0]['gems'] += 1
                    else:
                        user['stats'][0]['hearts'] += 1
                    collection.update_one({'_id': user_id}, {'$set': user})

                return jsonify({'message': 'Task status toggled successfully', 'all_tasks_completed': all_tasks_completed})
            else:
                return jsonify({'error': 'Failed to toggle task status'}), 500
        else:
            return jsonify({'error': 'Task not found'}), 404

            
    except Exception as e:
        # print(str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/user-pomo-rating', methods=['POST'])
def user_pomo_rating():
    try:
        collection = db['suggestions_data']
        data = request.json
        rating = data.get('rating')
        sequence = data.get('sequence')
        print(sequence)

        total_usage_hours = session.get('total_usage_hours')

        # Store data in MongoDB
        result = collection.insert_one({
            "Pomodoro Sequence": sequence,
            "Total Usage Hours": total_usage_hours,
            "Rating": rating
        })

        return jsonify({'message': 'Rating stored successfully', 'id': str(result.inserted_id), 'seq':sequence})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/create-streak', methods=['POST'])
def createStreak():
    try:
        collection = db['streaks']
        data = request.json
        print(data)
        user_name = session.get('username')
        friend_name = data.get('friend_name')
        print(friend_name)

        streak_data = {
            "user_id": user_name,
            "friend_id": friend_name,
            "start_date": datetime.now(),
            "last_interaction_dates": [[user_name, 0], [friend_name, 0]],  # Track last interaction date for each user
            "current_streak_lengths": 0,
            "max_streak_lengths": 0,  # Track max streak length for each user
            "active": 0
        }

        # Insert streak document into MongoDB
        result = collection.insert_one(streak_data)
        db.users.update_one(
            {"username": user_name},  # Match documents where username equals the provided username
            {"$push": {"streaks_with": friend_name}}  # Append user_name to the streaks_with array
        )
        db.users.update_one(
            {"username": friend_name},  # Match documents where username equals the provided username
            {"$push": {"streaks_with": user_name}}  # Append user_name to the streaks_with array
        )

        createNotification(session.get('username'),friend_name, 3)


        return jsonify({'message': 'Streak created successfully', 'id': str(result.inserted_id)})

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500
    
@app.route('/send-streak', methods=['POST'])
def sendStreak():
    try:
        data = request.json
        streak_id = data.get('streak_id')
        current_user = session.get('username')
        collection = db['dailys']
        all_tasks_completed = all(task.get('completed', 0) == 1 for task in collection.find({'createdBy': session.get('user_id')}))
        # Fetch streak document by its _id
        streak = db.streaks.find_one({'_id': ObjectId(streak_id)})
        if streak:
            # Determine the index of the current user in the last_interaction_dates array
            user_index = 0 if streak['last_interaction_dates'][0][0] == current_user else 1
            
            # Check if the last interaction date is set to zero (initial value)
            if streak['last_interaction_dates'][user_index][1] == 0:
                # Set the last interaction date to the current time
                streak['last_interaction_dates'][user_index][1] = datetime.now()
            else:
                # Check when the streak was last updated for the current user
                last_update_time = streak['last_interaction_dates'][user_index][1]
                time_difference = datetime.now() - last_update_time
                if time_difference <= timedelta(1):
                    # Streak was updated within the last 24 hours, do not increment streak count
                    return jsonify({'message': 'Streak already updated within the last 24 hours'})
            
            # Update the last interaction date for the current user
            streak['last_interaction_dates'][user_index][1] = datetime.now()
            
            # Check if both users have sent streaks to each other within the past 24 hours
            other_user_index = 1 - user_index  # Index of the other user in the last_interaction_dates array
            last_interaction_date = streak['last_interaction_dates'][other_user_index][1]
            if last_interaction_date != 0:
                time_difference = datetime.now() - last_interaction_date
                if time_difference <= timedelta(days=1):
                    # Both users have sent streaks to each other within 24 hours, increase streak count
                    streak['current_streak_lengths'] += 1
                    
                    # Update the max streak length if the current streak is longer
                    if streak['current_streak_lengths'] > streak['max_streak_lengths']:
                        streak['max_streak_lengths'] = streak['current_streak_lengths']
                        db.users.update_one({'_id': ObjectId(session.get('user_id'))}, {'$set'})
                else:
                    # Streak is broken, reset streak count to 0
                    streak['current_streak_lengths'] = 0

            # Update the streak document in the database
            db.streaks.update_one({'_id': ObjectId(streak_id)}, {'$set': streak})
            
            return jsonify({'message': 'Streak updated successfully'})
        else:
            return jsonify({'error': 'Streak not found'})

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

def time_difference_to_string(start_time, end_time):
    time_diff = end_time - start_time

    # Calculate days, hours, and minutes
    days = time_diff.days
    hours, remainder = divmod(time_diff.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    # Convert to string representation based on magnitude
    if days > 0:
        if hours == 0:
            return f"{days} days"
        elif hours == 1:
            return f"{days} days and 1 hour"
        else:
            return f"{days} days and {hours} hours"
    elif hours > 0:
        if minutes == 0:
            return f"{hours} hours"
        elif minutes == 1:
            return f"{hours} hours and 1 minute"
        else:
            return f"{hours} hours and {minutes} minutes"
    else:
        return f"{minutes} minutes"

@app.route('/get-streaks', methods=['GET'])
def get_streaks():
    try:
        collection = db['streaks']
        # Get the username from the session
        user_name = session.get('username')
        
        # Fetch streaks for the user from MongoDB
        user_streaks = list(collection.find({'$or': [{'user_id': user_name}, {'friend_id': user_name}]}))
        # Convert ObjectId to string for JSON serialization
        for streak in user_streaks:
            streak['_id'] = str(streak['_id'])
            # print(streak)
            
            if(session.get('username') == streak['user_id']):
                streak['friend'] = streak['friend_id']
                if streak['last_interaction_dates'][1][1] == 0:
                    streak['received_time'] = "Start a journey!"
                else:
                    streak['received_time'] = time_difference_to_string(streak['last_interaction_dates'][0][1], datetime.now())
            else:
                streak['friend'] = streak['user_id']
                if streak['last_interaction_dates'][0][1] == 0:
                    streak['received_time'] = "Start a journey!"
                else:
                    streak['received_time'] = time_difference_to_string(streak['last_interaction_dates'][1][1], datetime.now())
        # Return the user's streaks as JSON response
        print(user_streaks)
        return jsonify(user_streaks)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get-streaks', methods=['POST'])
def getUserLongestStreakWith():
    # Get the username from the session
    collection = db['streaks']
    current_user = session.get('username')
    # Get the username from the POST request
    data = request.get_json()
    search_username = data.get('username')

    # Search for streaks where the search username is either user_id or friend_id
    streak = collection.find_one({
        "$and": [
            {"$or": [
                {"user_id": current_user},
                {"friend_id": current_user}
            ]},
            {"$or": [
                {"user_id": search_username},
                {"friend_id": search_username}
            ]}
        ]
    })  

    if streak:
        if streak['user_id'] == current_user or streak['friend_id'] == current_user:
            max_streak = streak.get('max_streak_lengths', "NA")
            return jsonify({'max_streak': max_streak})
        else:
            return jsonify({'max_streak': "NA"})
    else:
        return jsonify({'max_streak': "NA"})
    
@app.route('/user_ranks', methods=['POST'])
def get_user_ranks():
    mode = request.json.get('mode', 0)  # Get mode from POST data
    users_collection = db['users']
    if mode == 0:
        # Fetch all users from MongoDB
        all_users = users_collection.find()
    elif mode == 1:
        # Get current user's friends list
        current_user_id = ObjectId(session.get('user_id'))
        current_user = users_collection.find_one({"_id": current_user_id})
        friends_list = current_user.get("friends", [])
        
        # Fetch data for friends only
        all_users = users_collection.find({"_id": {"$in": friends_list}})

    # Create a list to store user ranks, usernames, and scores
    user_ranks = []

    # Iterate over each user and append their rank, username, and score to the list
    for user in all_users:
        rank = user["daily_tasks_data"][0].get("userRank", 0)
        username = user.get("username", "")
        score = user["daily_tasks_data"][0].get("userScore", 0)
        user_ranks.append({"rank": rank, "username": username, "score": score})

    # Sort the user ranks list based on ranks (ascending order)
    user_ranks.sort(key=lambda x: x["rank"])

    # Return the sorted user ranks list as JSON
    return jsonify(user_ranks,session.get('username'))

def convert_to_h_m(hours):
    # Calculate the hours and minutes
    h = int(hours)
    m = int((hours - h) * 60)
    # Format the time as "h:m"
    # return f"{h}:{m}"
    return f"{h}:{m:02d}"

def get_last_n_elements(arr):
    if len(arr) <= 9:
        return arr
    else:
        return arr[-9:]

@app.route('/pomodoro-times', methods=['GET'])
def get_pomodoro_times():
    try:
        users_collection = db['users']
        user_id = ObjectId(session.get('user_id'))  # Replace with actual user identifier
        user = users_collection.find_one({'_id': user_id})

        pomodoro_stat = user.get('pomodoro_stat', [])
        total_time = user.get('pomodoro_usage_hours')
        total_time = convert_to_h_m(total_time)
        todays_time = convert_to_h_m(user.get('todays_pomo'))
        while len(pomodoro_stat) < 9:
            pomodoro_stat.insert(0, 0)

        print(pomodoro_stat)

        formatted_pomodoro_times = []
        for time in pomodoro_stat:
            formatted_time = convert_to_h_m(time)  # Use the function you provided
            formatted_pomodoro_times.append(formatted_time)
        print(formatted_pomodoro_times, total_time)
        formatted_pomodoro_times.append(todays_time)
        formatted_pomodoro_times.reverse()
        return jsonify(formatted_pomodoro_times, total_time)

    except Exception as e:
        # Handle any exceptions that occur during the process
        print(e)
        return jsonify({'error': str(e)}), 500

@app.route('/daily_task_insights', methods=['GET'])
def getDailyTasksInsights():
    try:
        # Access the users collection
        users_collection = db['users']

        # Get the current user's ID from the session
        user_id = session.get('user_id')

        # Find the current user's document in the users collection
        user = users_collection.find_one({'_id': ObjectId(user_id)})
        # Get the necessary data for task insights
        todays_task = user.get('todays_task')
        task_stat = user.get('task_stat', [])
        while len(task_stat) < 9:
            task_stat.insert(0, {'complete': 0, 'total': 0})

        # Add ocde for counting total no. ofdays completd here

        # Calculate total completed tasks and total days
        # completed_tasks = todays_task['complete']
        # total_days = len(task_stat)
        # print(task_stat)
        # print("THis is task stat...................")
        task_stat.append(todays_task)
        total_completed_days = sum(1 for task in task_stat if task['complete'] == task['total'])

# Calculate total number of days
        total_days = len(task_stat)

        # Get the last 10 days' task data
        last_10_tasks = task_stat[-10:]
        last_10_tasks.reverse()

        # Construct the response data
        # print(last_10_tasks)
        # Return the task insights data as JSON response
        response_data = {
            "last_10_tasks": last_10_tasks,
            "total_completed_days": total_completed_days,
            "total_days": total_days
        }

        return jsonify(response_data)

    except Exception as e:
        # Handle any errors that occur
        print(e)
        return jsonify({'error': str(e)}), 500

@app.route('/mission')
def mission():
    # Assuming mission.html is located in the templates folder
    return render_template('mission.html')
# 
# Main() function of app
# 
if __name__ == '__main__':
    app.run(debug=True, port=8888)

