from datetime import datetime
import bcrypt
from bson.objectid import ObjectId
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from flask import Flask, jsonify, render_template, request, redirect, session, url_for
import secrets

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
db = client["LearnSyncDatabase"]

# 
# Supporting Functions for Front-end & other Main Func's()
# 

# Function for creating user
def createUser(username, password):
    collection = db["users"]
    
    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    new_user = {
        "username": username,
        "password": hashed_password,
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
                "completed":0
            }
        ],
        "pomodoro_sequences":[
            [25.0,5.0,25.0,5.0,25.0,30.0],
            [60.0,10.0,60.0,10.0,60.0,30.0],
            [75.0,15.0,45.0,10.0,30.0,60.0]
        ]
    }

    new_user = collection.insert_one(new_user)
    return new_user

# Fuction to Create Varous types of request
def createRequest(from_user, to_user, type):
    request_types = {
        0:'Friend Request',
        1:'Streak Request',
        2:'Invite To Group'
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

@app.route('/check-username-availability', methods=['POST'])
def check_username_available():
    collection = db["users"]
    username = request.form.get('username')
    user = collection.find_one({'username': username})
    if user:
        return jsonify({'message': 'Username already exists'}), 409
    else:
        return jsonify({'message': 'Username available'}), 200

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
@app.route('/sign-up', methods=['POST','GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = createUser(username, password)
        # user_id = str(user.inserted_id)
        # user = fetch_user_by_id(user_id)
        # print(user)
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
    flashcards_cursor = collection.find({})
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
    cursor = collection.find(query)
    # Convert ObjectId to string and format the results
    flashcards = [flashcard for flashcard in cursor]
    for flashcard in flashcards:
        flashcard['_id'] = str(flashcard['_id'])
    # print(flashcards)
    return jsonify(flashcards)

@app.route('/search_flashcards', methods=['POST'])
def search_flashcards():
    keyword = request.json.get('keyword')
    collection = db["flashcards"]
    # Search for the keyword in the name or category fields using a case-insensitive regular expression
    query = {
        "$or": [
            # {"name": {"$regex": keyword, "$options": "i"}},
            # {"category": {"$regex": keyword, "$options": "i"}},
            # {"flashcard_data": {"$elemMatch": {"$elemMatch": {"$regex": keyword, "$options": "i"}}}},
            {"hashtags": {"$regex": keyword, "$options": "i"}}
        ]
    }
    # Fetch all flashcards that match the query
    cursor = collection.find(query)
    # Convert ObjectId to string and format the results
    flashcards = [flashcard for flashcard in cursor]
    for flashcard in flashcards:
        flashcard['_id'] = str(flashcard['_id'])
    return jsonify(flashcards)



#
# Hey Friends Functionality Goes Here...
# 

# Function for add friend fuctionality
@app.route("/add-friend/<user_id>", methods=['POST'])
def addFriend(user_id):
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

@app.route('/update-daily-task', methods=['POST'])
def updateDailyTasks():
    pass

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
    print(userId)
    # print(request)
    # user_id = request.form.get('userId')
    user_id = userId
    user_stats = fetch_user_stats(user_id)
    print(user_stats, "user stats")
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
    print(user)
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
    sequences = [[float(num) for num in seq.split(',')] for seq in sequences]

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


# 
# Main() function of app
# 
if __name__ == '__main__':
    app.run(debug=True, port=8888)
