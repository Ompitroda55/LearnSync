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

# createDailyTask("Om's Task", 2)
    
def findGroupsContainingMembers(member1, member2):
    # Initialize an empty list to store the groups containing both members
    matching_groups = []

    # Query the groups collection
    collection = db['groups']
    groups = collection.find()

    # Iterate through each group
    for group in groups:
        # Check if both members are present in the group's members list
        if member1 in group['members'] and member2 in group['members']:
            matching_groups.append(group)

    return matching_groups[0]['name']

# Example usage:
import pandas as pd
import numpy as np

# Generate sample data
np.random.seed(0)  # for reproducibility

# Generate random Pomodoro sequences
num_sequences = 1000
sequences = []
ratings = []

for _ in range(num_sequences):
    sequence_length = np.random.randint(1, 7)  # Random sequence length between 1 and 6
    sequence = ','.join(str(np.random.randint(1, 61)) for _ in range(sequence_length))  # Generate sequence
    sequences.append(sequence)
    # Generate random rating for each sequence
    ratings.append(np.random.randint(1, 6))

# Create DataFrame
data = pd.DataFrame({'Pomodoro Sequence': sequences, 'Rating': ratings})

# Save data to CSV
data.to_csv('sample_pomodoro_data.csv', index=False)

