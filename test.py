from datetime import datetime, timedelta
from pymongo import MongoClient
from bson.objectid import ObjectId
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

riddles = [
    {"question": "What has keys but can't open locks?", "answer": "Keyboard 🔑"},
    {"question": "What comes once in a minute, twice in a moment, but never in a thousand years?", "answer": "The letter 'm' ⏰"},
    {"question": "What has a head and a tail, but no body?", "answer": "A coin 🐍"},
    {"question": "What has many eyes, yet can't see?", "answer": "Potato 🥔"},
    {"question": "What has a neck but no head?", "answer": "Bottle 🍾"},
    {"question": "What is full of holes but still holds water?", "answer": "Sponge 🧽"},
    {"question": "What can travel around the world while staying in a corner?", "answer": "Stamp 🌍"},
    {"question": "What belongs to you, but other people use it more than you do?", "answer": "Your name 📝"},
    {"question": "What is always in front of you but can't be seen?", "answer": "Future 🔮"},
    {"question": "What has a mouth but never eats, has a bed but never sleeps?", "answer": "River 🏞️"},
    {"question": "What can you catch but not throw?", "answer": "Cold 🤒"},
    {"question": "What has a bottom at the top?", "answer": "Legs 👖"},
    {"question": "What has cities but no houses, forests but no trees, and rivers but no water?", "answer": "Map 🗺️"},
    {"question": "What has a head, a tail, is brown, and has no legs?", "answer": "Penny 💰"},
    {"question": "What has a heart that doesn't beat?", "answer": "Artichoke 🍴"},
    {"question": "What has one eye but can't see?", "answer": "Needle 👁️"},
    {"question": "What has a face and two hands but no arms or legs?", "answer": "Clock ⏰"},
    {"question": "What has keys but can't open doors?", "answer": "Piano 🎹"},
    {"question": "What is so fragile that saying its name breaks it?", "answer": "Silence 🤫"},
    {"question": "What starts with 'e' and ends with 'e' but only has one letter?", "answer": "Envelope ✉️"},
    {"question": "What can you break without touching it?", "answer": "Promise 🤝"},
    {"question": "What has a thumb and four fingers but is not alive?", "answer": "Glove 🧤"},
    {"question": "What has a tail and a head but no body?", "answer": "Coin 🐟"},
    {"question": "What is so delicate that saying its name breaks it?", "answer": "Silence 🤭"},
    {"question": "What is at the end of a rainbow?", "answer": "W 🌈"},
    {"question": "What is as light as a feather, yet even the strongest man cannot hold it for long?", "answer": "Breath 💨"},
    {"question": "What gets wetter as it dries?", "answer": "Towel 🧼"},
    {"question": "What has one eye but cannot see?", "answer": "Needle 👁️"},
    {"question": "What has hands but can't clap?", "answer": "Clock ⏰"},
    {"question": "What is always in bed but never sleeps?", "answer": "River 🛌"},
    {"question": "What is full of holes but can still hold water?", "answer": "Sponge 🌊"},
    {"question": "What is at the end of every rainbow?", "answer": "Letter W 🌈"},
    {"question": "What can be cracked, made, told, and played?", "answer": "Joke 😄"},
    {"question": "What has one head, one foot, and four legs?", "answer": "Bed 🛏️"},
    {"question": "What has hands but cannot clap?", "answer": "Clock ⏰"},
    {"question": "What has keys but can't open locks?", "answer": "Keyboard 🔑"},
    {"question": "What is always in front of you but can't be seen?", "answer": "Future 🔮"},
    {"question": "What has a neck but no head?", "answer": "Bottle 🍾"},
    {"question": "What comes once in a minute, twice in a moment, but never in a thousand years?", "answer": "The letter 'm' ⏰"},
    {"question": "What belongs to you but other people use it more than you do?", "answer": "Your name 📝"},
    {"question": "What is easy to get into but hard to get out of?", "answer": "Trouble 😅"},
    {"question": "What runs all around a backyard, yet never moves?", "answer": "Fence 🏡"},
    {"question": "What has to be broken before you can use it?", "answer": "Egg 🥚"},
    {"question": "What has keys but can't open locks?", "answer": "Piano 🎹"},
    {"question": "What is black when you buy it, red when you use it, and gray when you throw it away?", "answer": "Charcoal 🖌️"},
    {"question": "What has a head and a tail but no body?", "answer": "Coin 🌓"},
    {"question": "What has many keys but can't open a single lock?", "answer": "Piano 🎹"},
    {"question": "What has hands but cannot clap?", "answer": "Clock ⏰"},
    {"question": "What can be cracked but is never held?", "answer": "Joke 😆"}
]



def upload_riddles_to_mongodb(riddles):
    # Connect to MongoDB
    uri = "mongodb+srv://admin:admin@learnsynccluster.el71bgq.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(uri, server_api=ServerApi('1'))
# client = MongoClient('mongodb://localhost:27017/')
    db = client["LearnSyncDatabase"]
    collection = db["riddles"]

    # Insert riddles into MongoDB
    collection.insert_many(riddles)
    print("Riddles uploaded successfully to MongoDB.")

# upload_riddles_to_mongodb(riddles)

previous_date = (datetime.now().date() - timedelta(days=1))
print(previous_date)
print(datetime.now().date() == (previous_date + timedelta(days=1)))
print()