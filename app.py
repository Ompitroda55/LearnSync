from datetime import datetime
from bson import ObjectId
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from flask import Flask, render_template, request, redirect, url_for
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

@app.route('/')
def index():
    return render_template('signup.html')

@app.route('/sign-up')
def signup():
    username = request.form['username']
    password = request.form['password']

    new_user = {
        "username": username,
        "password": password,
    }

    # 
    # To create a new users collection and further operations
    # 
    # insert_result = users_collection.insert_one(new_user)


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

if __name__ == '__main__':
    app.run(debug=True, port=8888)
