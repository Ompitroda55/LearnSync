import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
 
# Load the existing data
data = pd.read_csv('pomodoro_data.csv')

# Preprocess the data
X = data[['hours']].values
y = data[['pomodoro_sequence']].values
y = np.reshape(y, (-1, 5))

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Define the neural network model
model = Sequential()
model.add(Dense(64, activation='relu', input_shape=(1,)))
model.add(Dense(64, activation='relu'))
model.add(Dense(5, activation='linear'))

# Compile the model
model.compile(optimizer='adam', loss='mse')

# Train the model
model.fit(X_train, y_train, epochs=100, batch_size=32, validation_data=(X_test, y_test))

# Evaluate the model
y_pred = model.predict(X_test)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
print(f'RMSE: {rmse:.2f}')

# Get the recommended pomodoro sequence for a user with 10 hours of usage
user_hours = 10
user_sequence = model.predict(user_hours.reshape(1, -1))
user_sequence = np.round(user_sequence).astype(int)

print(f'Recommended pomodoro sequence for user with {user_hours} hours of usage: {user_sequence}')