import time
from apscheduler.schedulers.background import BackgroundScheduler
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime, timedelta

# MongoDB connection
uri = "mongodb+srv://admin:admin@learnsynccluster.el71bgq.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, server_api=ServerApi('1'))
# client = MongoClient('mongodb://localhost:27017/')
db = client["LearnSyncDatabase"]

def reset_completed_tasks():
    # Update the "completed" field to 0 for all documents in the "dailys" collection
    db.dailys.update_many({}, {"$set": {"completed": 0}})

# reset_completed_tasks()
# Scheduler setup
# scheduler = BackgroundScheduler()
# scheduler.add_job(reset_completed_tasks, 'cron', hour=0, minute=0)  # Schedule job daily at 24:00
# scheduler.start()

# Keep the script running
# try:
#     while True:
#         pass
# except (KeyboardInterrupt, SystemExit):
#     scheduler.shutdown()

def check_streaks():
    # Retrieve documents from the collection
    collection = db['streaks']
    streaks = collection.find()

    # Iterate over each document
    for streak in streaks:
        # Extract last interaction dates for both users
        user1_last_interaction = streak['last_interaction_dates'][0][1]
        user2_last_interaction = streak['last_interaction_dates'][1][1]

        # Calculate the time difference
        time_difference = abs(user1_last_interaction - user2_last_interaction)
        print(time_difference)

        # If the time difference is less than 18 hours, set active to 1
        if time_difference < timedelta(hours=18):
            collection.update_one({'_id': streak['_id']}, {'$set': {'active': 1}})
        time.sleep(60)

while True:
    check_streaks()