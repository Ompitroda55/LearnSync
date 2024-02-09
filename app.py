from datetime import datetime
from bson.objectid import ObjectId
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from flask import Flask, jsonify, render_template, request, redirect, url_for
# from flask_ngrok import run_with_ngrok

app = Flask(__name__)
# run_with_ngrok(app)

# MongoDB Stuff
uri = "mongodb+srv://admin:admin@learnsynccluster.el71bgq.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["LearnSyncDatabase"]


from flask import Flask, request, render_template

app = Flask(__name__)

#
# Code for Login and Homepage
#
@app.route('/check-credentials', methods=['POST'])
def checkCredentials():
    collection = db["users"]
    username = request.form.get('username')
    password = request.form.get('password')
    print("User password : " + password, username)
    user = collection.find_one({'username': username})
    # print(user['password'])
    if user:
        if password == user['password']:
            return jsonify({'message': 'Valid Creds'}), 200
        else:
            return jsonify({'message': 'Incorrect Password'}), 400
  
    else:
        return jsonify({'message': 'Username not available'}), 400

# Code to handle login request

@app.route('/login', methods=['GET', 'POST'])
def login():
    collection = db["users"]
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        print(username, password)
        user = collection.find_one({'username': username})
        requests = get_requests_for_receiver(str(user['_id']))
        print(requests)
        return render_template('dashboard.html', user=user, requests=requests)
    else:
        return render_template('home_alt.html')

# Code for inserting flashcard created by user

@app.route('/insert-flash-card', methods=['POST'])
def create_FC():
    data = []
    name = request.form['name']
    subject = request.form['subject']
    questions = request.form.getlist('question[]')
    answers = request.form.getlist('answer[]')
    for i in range(len(min(questions,answers))):
        data.append((questions[i], answers[i]))
    print(data)
    createFlashCard(name, subject, data)
    return redirect(url_for('flashCardApp'))

# Helper function to create flashcard in DB

def createFlashCard(name, category, flashcard_data):
    collection = db["flashcards"]
    new_flashcard_pack = {
        "name" : name,
        "category" : category,
        # "created_by": ObjectId("your_user_object_id"),  # Replace with actual ObjectId of the user
        "created_at": datetime.utcnow().strftime('%Y-%m-%d'),
        "times_opened": 0,
        "flashcard_data": flashcard_data
    }
    insert_result = collection.insert_one(new_flashcard_pack)

    # Retrieve ObjectId of inserted document
    id = insert_result.inserted_id

    return id


# Main Entry Point

@app.route('/')
def index():
    return render_template('home_alt.html')

#
# User Signup Stuff
#

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

# Social Stuff
    
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
        "status": "pending"
    }
    new_request = collection.insert_one(new_request)
    print(new_request)
    return new_request

# Function to Create user in DB

def createUser(username, password):
    collection = db["users"]
    
    new_user = {
        "username": username,
        "password": password,
        "stats": [
            {
                "streaks":0,
                "gems":0,
                "hearts":0
            }
        ], 
        "groups": [],
        "friends": []
    }

    new_user = collection.insert_one(new_user)
    return new_user


# Function to Handle Signup

@app.route('/sign-up', methods=['POST','GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = createUser(username, password)
        user_id = str(user.inserted_id)
        user = fetch_user_by_id(user_id)
        print(user)
        return render_template('home_alt.html')
    else:
        return render_template('signup.html')

#
# All code stuff for Flashcards goes here
#

# Main windows of FlashCard section of app

@app.route('/flash_card')
def flashCardApp():
    categories = ["Literature", "Mathematics", "Science", "History", "Geography", "Computer Science", "Art", "Music", "Health", "Business", "Test Preparation", "Miscellaneous"]

    # questions_answers = [
    # ("What is the capital of India?", "New Delhi"),
    # ("What is the capital of Australia?", "Gundi Gathiya")
    # ]
    collection = db["flashcards"]
    flashcards = collection.find({})

    print(flashcards)
    # id = createFlashCard("A","B",questions_answers)
    return render_template('flash_cards.html', id=id, flashcards=flashcards)

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
    print(times_opened)
    print(type(flashcard))
    return flashcard

# Function for opening a particular flashcard

@app.route('/flashcard/<flashcard_id>')
def view_flashcard(flashcard_id):
    flashcard = fetch_flashcard_by_id(flashcard_id)
    return render_template('view_flashcard.html', flashcard=flashcard)

#
# Everything for Dashboard goes here
# 

# Function to fetch object of user from its object_id

def fetch_user_by_id(user_id):
    collection = db["users"]
    user_object_id = ObjectId(user_id)
    user = collection.find_one({"_id": user_object_id})
    print(type(user))
    return user

# Function for add friend fuctionality

@app.route("/add-friend/<user_id>", methods=['POST'])
def addFriend(user_id):
    user = fetch_user_by_id(user_id)
    friend_username = request.form['friend-username']
    print(friend_username)
    print(user['username'] + "Is the user name")
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
    

def get_requests_for_receiver(receiver_id):
    collection = db["requests"]
    receiver_object_id = ObjectId(receiver_id)
    receiver = fetch_user_by_id(receiver_object_id)
    print(receiver, "It is receiver")
    requests = list(collection.find({"receiver": receiver['username'], "status": "pending"}))
    print(requests)
    return requests


def get_requests_sender_or_receiver(object_id):
    collection = db["requests"]
    object_id = ObjectId(object_id)
    requests = list(collection.find({"$or": [{"sender": object_id}, {"receiver": object_id}]}))
    return requests

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

@app.route("/", methods=['POST'])
def todo1():
    if request.method == "POST":   # if the request method is post, then insert the todo document in todos collection
        content = request.form['content']
        degree = request.form['degree']
        todos.insert_one({'content': content, 'degree': degree})
        return redirect(url_for('todo1')) # redirect the user to home page
    all_todos = todos.find()    # display all todo documents
    return render_template('dashboard.html', todos = all_todos) # render home page template with all todos
#Delete Route
@app.post("/<id>/delete/")
def delete(id): #delete function by targeting a todo document by its own id
    todos.delete_one({"_id":ObjectId(id)}) #deleting the selected todo document by its converted id
    return redirect(url_for('todo1')) # again, redirecting you to the home page 
db = client.LearnSyncDatabase # creating your flask database using your mongo client 
todos = db.todos # creating a collection called "todos"


@app.route("/reject-friend-request/<request_id>", methods=['POST'])
def reject_friend_request(request_id):
    collection = db["requests"]
    request_object_id = ObjectId(request_id)
    # Update the status of the request to rejected
    collection.update_one({"_id": request_object_id}, {"$set": {"status": "rejected"}})
    return jsonify({'message': 'Friend request rejected successfully'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=8888)
