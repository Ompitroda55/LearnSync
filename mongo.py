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

def save_to_mongodb(df, db_name, collection_name):
    # Connect to MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client[db_name]
    collection = db[collection_name]

    # Convert DataFrame to dictionary
    data = df.to_dict(orient='records')

    # Insert data into MongoDB collection
    collection.insert_many(data)

    print("Data saved to MongoDB collection '{}' in database '{}'.".format(collection_name, db_name))

import pandas as pd
# from pymongo import MongoClient

# # Read the CSV file into a DataFrame
# data = pd.read_csv('sample_pomodoro_data.csv')

# # Convert DataFrame to a list of dictionaries
# data_dicts = data.to_dict(orient='records')

# collection = db['suggestions_data']  # Specify your collection name

# collection.insert_many(data_dicts)

import pandas as pd
import numpy as np
import tensorflow as tf
from pymongo import MongoClient

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

# Connect to MongoDB
collection = db['suggestions_data']  # Change 'your_collection_name' to your actual collection name

# Example usage:
suggested_sequence = suggest_pomodoro_sequence(60, collection, tolerance=5)

if suggested_sequence:
    print("Suggested Pomodoro Sequence:", suggested_sequence)
else:
    print("No suitable sequence found for the given total usage hours within the specified tolerance.")
