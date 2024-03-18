from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime

uri = "mongodb+srv://admin:admin@learnsynccluster.el71bgq.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, server_api=ServerApi('1'))
# client = MongoClient('mongodb://localhost:27017/')
db = client["LearnSyncDatabase"]

def createDailyTask(task_name, task_priority):
    # Select the collection
    collection = db["dailys"]

    # Create a new task document
    new_task = {
        "createdBy": task_name,
        "creationDate": datetime.now(),
        "task_name": task_name,
        "priority": task_priority,
        "completed": 0,  # Assuming 0 means task is not completed, adjust as needed
        "lastCompleted": 0  # Assuming initial value for lastCompleted, adjust as needed
    }

    try:
        # Insert the new task document into the collection
        result = collection.insert_one(new_task)
        print("New task created with ID:", result.inserted_id)
        return result.inserted_id  # Return the ID of the newly inserted document
    except Exception as e:
        print("Error creating task:", e)
        return None

createDailyTask("Om's Task", 2)