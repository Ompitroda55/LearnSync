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
        # time.sleep(60)

def update_pomodoro_stat():
    users_collection = db['users']
    # Iterate over each user in the collection
    for user in users_collection.find():
        # Get the todays_pomo value from the user document
        todays_pomo = user.get("todays_pomo", 0)
        
        # Update the pomodoro_stat array by pushing todays_pomo value
        users_collection.update_one({"_id": user["_id"]}, {"$push": {"pomodoro_stat": todays_pomo}})
        
        print(f"Updated pomodoro_stat for user: {user['_id']}")

# Call the function to update pomodoro_stat for all users

def update_task_stat_for_all_users():
    try:
        # Access the users collection
        users_collection = db['users']

        # Get all users from the collection
        all_users = users_collection.find()

        # Iterate over each user
        for user in all_users:
            user_id = user['_id']

            # Create todays_task object
            sample_task = {'complete': 0, 'total': 0}  # Initialize with default values
            todays_task = user['todays_task']
            # Update task_stat array
            print(str(user['todays_task']['total']) + "is for user " + user['username'])
            if(user['todays_task']['total']> 0):
                users_collection.update_one(
                    {'_id': user_id},
                    {'$push': {'task_stat': todays_task}},
                )

            users_collection.update_one(
                {'_id': user_id},
                {'$set': {'todays_task': sample_task}}
            )

        print("Task stat updated for all users successfully.")

    except Exception as e:
        print(f"Error: {str(e)}")

def update_todays_task_for_all_users():
    try:
        # Assuming db is the MongoDB database connection
        dailys_collection = db['dailys']
        users_collection = db['users']

        # Get all users from the collection
        all_users = users_collection.find()

        # Iterate over each user
        for user in all_users:
            user_id = user['_id']

            # Find tasks created by the user
            user_tasks = dailys_collection.find({"createdBy": user_id})

            # Count the total and completed tasks
            total_tasks = dailys_collection.count_documents({"createdBy": user_id})
            completed_tasks = dailys_collection.count_documents({"createdBy": user_id, "completed": 1})

            # Create todays_task object
            todays_task = {"complete": completed_tasks, "total": total_tasks}

            # Update the user document with today's task data
            users_collection.update_one({"_id": user_id}, {"$set": {"todays_task": todays_task}})

        print("Today's task updated for all users successfully.")

    except Exception as e:
        print(f"Error: {str(e)}")

def update_highest_rank():
    users_collection = db['users']
    # Iterate through each user in the collection
    for user in users_collection.find():
        # Get the current user's highest rank
        highest_rank = user['daily_tasks_data'][0].get('highestRank')

        # Get the user's current rank
        current_rank = user['daily_tasks_data'][0].get('userRank')

        # Update the user's highest rank if the current rank is lower
        if current_rank < highest_rank:
            users_collection.update_one(
                {'_id': user['_id']},
                {'$set': {'highestRank': current_rank}}
            )

    print("Highest ranks updated successfully.")

def calculate_task_scores():
    users_collection = db['users']
    # Iterate through each user in the collection
    for user in users_collection.find():
        # Get the total number of days and completed tasks
        task_stat = user.get('task_stat')
        total_days = len(task_stat)
        completed_tasks = sum(task['complete'] for task in task_stat)
        total_tasks = 0
        total_completes = 0
        print(task_stat)
        for task in task_stat:
            if task['total']>0 and task['complete']:
                if task['complete']==task['total']:
                    total_completes+=task['complete']
                total_tasks+=task['total']

            else:
                total_tasks+=1
                total_completes+=1
        print(total_completes)
        print(total_tasks)
        print()
        # Calculate the completion percentage
        completion_percentage = total_completes / total_tasks if total_days > 0 else 0


        # Assign a score based on the completion percentage
        # You can define your scoring logic here
        score = int(completion_percentage * 100)


        # Update the user's score in the database
        users_collection.update_one(
            {'_id': user['_id']},
            {'$set': {'daily_tasks_data.0.taskScore': score}}
        )
        print(f"For completing {completed_tasks} from {total_tasks} {user['username']} got {score}")

    print("Task scores calculated and updated successfully.")

def calculate_score(stats):
    # Extract stats values
    streaks = max(stats[0].get("streaks", 0), 1)
    gems = max(stats[0].get("gems", 0), 1)
    hearts = max(stats[0].get("hearts", 0), 1)
    longest_streak = max(stats[0].get("longest_streak", 0), 1)

    # Assign weights to stats
    streaks_weight = 0.3
    gems_weight = 0.2
    hearts_weight = 0.2
    longest_streak_weight = 0.3

    # Calculate total score based on weighted sum of stats
    total_score = (streaks * streaks_weight) + (gems * gems_weight) + (hearts * hearts_weight) + (longest_streak * longest_streak_weight)

    return int(total_score)

def update_all_user_ranks():
    users_collection = db['users']
    # Fetch all users from MongoDB
    all_users = users_collection.find()

    # Create a 2D array to store user scores and usernames
    user_scores = []

    for user in all_users:
        # Calculate score for each user
        score = calculate_score(user.get("stats", {}))
        username = user.get("username")

        # Append username and score to the array
        user_scores.append([username, score])

    # Sort the user scores array based on scores (descending order)
    user_scores.sort(key=lambda x: x[1], reverse=True)

    # Assign ranks based on the sorted order
    for rank, (username, score) in enumerate(user_scores, start=1):
        # Update userScore field
        users_collection.update_one(
            {"username": username},
            {"$set": {"daily_tasks_data.0.userScore": score}}
        )

        # Update userRank field with current rank
        users_collection.update_one(
            {"username": username},
            {"$set": {"daily_tasks_data.0.userRank": rank}}
        )

        print(f"For Score: {score} user {username} got rank {rank}")



update_all_user_ranks()

# Call the function to calculate task scores
calculate_task_scores()


update_highest_rank()

update_todays_task_for_all_users()


#update_task_stat_for_all_users() # yeh raat ko chalega


update_pomodoro_stat()
check_streaks()
reset_completed_tasks()

update_todays_task_for_all_users()