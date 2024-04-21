from datetime import datetime
import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


uri = "mongodb+srv://admin:admin@learnsynccluster.el71bgq.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["LearnSyncDatabase"]
users_collection = db['users']

new_user_structure = {
    "stats": [{"streaks": 0, "gems": 0, "hearts": 0}],
    "groups": [],
    "friends": [],
    "streaks_with": [],
    "daily_tasks_data": [{"lastComplete": 0, "daysCompletes": [], "longestStreak": 0, "userRank": 0, "userScore": 0, "experience": "rookie", "highestRank": 10000, "taskScore":0}],
    "todays_pomo": 0,
    "todays_task":{'complete':0, 'total':0},
    "task_stat":[],
    "pomodoro_stat": [],
    "consecutive_login": 0,
    "last_login": datetime.now(),
    "pomodoro_sequences": [[25.0, 5.0, 25.0, 5.0, 25.0, 30.0], [60.0, 10.0, 60.0, 10.0, 60.0, 30.0], [75.0, 15.0, 45.0, 10.0, 30.0, 60.0]],
    "joinging_date": datetime.now(),
    "pomodoro_usage_hours": 0.0
}

# Iterate over each user in the collection
for user in users_collection.find():
    # Check if the user has all fields from the new_user_structure
    for key, value in new_user_structure.items():
        if key not in user:
            # Add the missing field to the user with default values
            users_collection.update_one({"_id": user["_id"]}, {"$set": {key: value}})
            print(f"Added missing field '{key}' for user: {user['username']}")