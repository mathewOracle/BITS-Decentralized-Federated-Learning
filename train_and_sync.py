import numpy as np
import pickle
import tensorflow as tf
import requests

# === Model ===
def create_model(input_shape=561, num_classes=6):
    model = tf.keras.Sequential([
        tf.keras.Input(shape=(input_shape,)),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(num_classes, activation='softmax')
    ])
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    return model

def train_model(X, y, model, epochs=2):
    history = model.fit(X, y, epochs=epochs, batch_size=32, verbose=0)
    loss = history.history['loss'][-1]
    acc = history.history['accuracy'][-1]
    return model, loss, acc

def get_weights(model):
    return pickle.dumps(model.get_weights())

def set_weights(model, data):
    weights = pickle.loads(data)
    model.set_weights(weights)

def gossip_sync(peer_url, model):
    try:
        r = requests.get(f"http://{peer_url}/weights", timeout=5)
        set_weights(model, r.content)
        print(f"Gossip sync successful with {peer_url}")
    except Exception as e:
        print(f"Failed gossip sync with {peer_url}: {e}")

# === Dataset ===
def load_uci_har_subject_data(subject_id):
    basepath="UCI_HAR_Dataset/"
    X = np.loadtxt(basepath+"train/X_train.txt")
    y = np.loadtxt(basepath+"train/y_train.txt") - 1
    subjects = np.loadtxt(basepath+"train/subject_train.txt").astype(int)
    print(f"Loaded for subject {subject_id}")
    mask = subjects == subject_id
    return X[mask], y[mask]
