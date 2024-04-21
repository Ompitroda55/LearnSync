from datetime import datetime
import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


uri = "mongodb+srv://admin:admin@learnsynccluster.el71bgq.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["LearnSyncDatabase"]
# Connect to MongoDB

def calculate_rank(stats):
    # Extract stats values
    streaks = stats[0].get("streaks", 0)
    gems = stats[0].get("gems", 0)
    hearts = stats[0].get("hearts", 0)
    longest_streak = stats[0].get("longest_streak", 0)

    # Assign weights to stats
    streaks_weight = 0.3
    gems_weight = 0.2
    hearts_weight = 0.2
    longest_streak_weight = 0.3

    # Calculate total score based on weighted sum of stats
    total_score = (streaks * streaks_weight) + (gems * gems_weight) + (hearts * hearts_weight) + (longest_streak * longest_streak_weight)

    # Ensure XP starts from 1 if all stats are zero
    if total_score == 0:
        total_score = 1

    return int(total_score)

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


# Update ranks for all users
update_all_user_ranks()


