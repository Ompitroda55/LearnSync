from datetime import datetime
from bson import ObjectId
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

def createFlashCard(name, category, flashcard_data):
    collection = db["flashcards"]
    new_flashcard_pack = {
        "name" : name,
        "category" : category,
        # "created_by": ObjectId("your_user_object_id"),  # Replace with actual ObjectId of the user
        "created_at": datetime.utcnow().strftime('%Y-%m-%d'),
        "times_opened": 10,
        "flashcard_data": flashcard_data
    }
    insert_result = collection.insert_one(new_flashcard_pack)

    # Retrieve ObjectId of inserted document
    id = insert_result.inserted_id

    return id


# Min Entry Point
@app.route('/')
def index():
    return render_template('signup.html')

#
# User Signup
#

@app.route('/check-username', methods=['POST'])
def check_username():
    collection = db["users"]
    username = request.form.get('username')
    user = collection.find_one({'username': username})
    if user:
        return jsonify({'message': 'Username already exists'}), 409
    else:
        return jsonify({'message': 'Username available'}), 200

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

@app.route('/sign-up', methods=['POST'])
def signup():
    username = request.form['username']
    password = request.form['password']
    user = createUser(username, password)
    # return  str(createUser(username, password)) + ' has been created.'
    return render_template('dashboard.html', user=user)
    # 
    # To create a new users collection and further operations
    # 
    # insert_result = users_collection.insert_one(new_user)

#
# All code stuff for Flashcards goes here
#

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
    print(type(flashcard))
    return flashcard

@app.route('/flashcard/<flashcard_id>')
def view_flashcard(flashcard_id):
    flashcard = fetch_flashcard_by_id(flashcard_id)
    return render_template('view_flashcard.html', flashcard=flashcard)

#
# Everything for Dashboard goes here
# 

def fetch_user_by_id(user_id):
    collection = db["users"]
    user_object_id = ObjectId(user_id)
    user = collection.find_one({"_id": user_object_id})
    print(type(user))
    return user

@app.route("/add-friend/<user_id>", methods=['POST'])
def addFriend(user_id):
    user = fetch_user_by_id(user_id)
    friend_id = request.form['friend-id']
    friend_id = ObjectId(db["users"].find_one({"username": friend_id})["_id"])
    # user_id = ObjectId(user_id)
    db["users"].update_one({"_id": user_id}, {"$push": {"friends": friend_id}})
    # return redirect(url_for('dashboard', user_id=user_id))
    return "Friend Added"
    
    













if __name__ == '__main__':
    app.run(debug=True, port=8888)
