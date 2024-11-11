import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout


input_dim = 5  
hidden_units1 = 128  
hidden_units2 = 64   


model = Sequential([
    Dense(hidden_units1, input_shape=(input_dim,), activation="relu"),
    Dropout(0.3),  
    Dense(hidden_units2, activation="relu"),
    Dropout(0.3),
    Dense(1, activation="sigmoid")  
])

model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])

X_train = np.loadtxt("AI-Models\output.txt")
print(X_train.shape)
Y_train = np.zeros(X_train.shape[0])
X_anomaly = np.loadtxt("AI-Models\output_abnormal.txt")
Y_anomaly = np.ones(X_anomaly.shape[0])

X = np.concatenate([X_train, X_anomaly], axis=0)
Y = np.concatenate([Y_train, Y_anomaly], axis=0)

model.fit(X, Y, epochs=20, batch_size=32, shuffle=True, validation_split=0.2)

model.save("saved_model.h5")

def detect_anomaly(data):
    predictions = model.predict(data)
    return predictions

print(detect_anomaly(np.loadtxt("output_abnormal.txt")[6:16]))