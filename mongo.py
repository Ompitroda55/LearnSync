from flask import jsonify, request
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


uri = "mongodb+srv://admin:admin@learnsynccluster.el71bgq.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["LearnSyncDatabase"]


# Send a ping to confirm a successful connection
def fetch_flashcards(criteria, value):
    # Select the flashcards collection
    collection = db["flashcards"]
    
    # Define a query dictionary based on the criteria
    query = {}
    if criteria == "username":
        query = {"created_by": value}  # Assuming the username is stored in the 'created_by' field
    elif criteria == "creation_date":
        query = {"created_at": value}  # Assuming the creation date is stored in the 'created_at' field
    elif criteria == "hashtags":
        query = {"hashtags": {"$in": [value]}}  # Assuming hashtags are stored as an array in the 'hashtags' field
    elif criteria == "category":
        query = {"category": value}
    elif criteria == "topic":
        query = {"name": {"$regex": value, "$options": "i"}}  # Case-insensitive search for topic
    else:
        flashcards = collection.find(query)
    # Execute the query and fetch the flashcards
    
    # Convert ObjectId to string and format the results
    formatted_flashcards = []
    for flashcard in flashcards:
        flashcard['_id'] = str(flashcard['_id'])
        formatted_flashcards.append(flashcard)
    
    return formatted_flashcards

# @app.route('/search_flashcards', methods=['POST'])
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

print(search_flashcards('to'))