import numpy as np
import pickle
import tensorflow as tf
import requests, urllib
import os
import io
import zipfile
import fastapi

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
    weights = model.get_weights()
    data = pickle.dumps(weights)
    return fastapi.responses.StreamingResponse(io.BytesIO(data), media_type="application/octet-stream")


def set_weights(model, data):
    weights_bytes = data
    weights = pickle.loads(weights_bytes)
    model.set_weights(weights)
    print(f"[Sync] Weights set from peer {peer_url}")
    return {"status": "weights updated", "layers": len(weights)}

def gossip_sync(peer_url, model):
    try:
        print(f"[Sync] Pulling weights from {peer_url}/weights")
        response = requests.get(f"http://{peer_url}/weights", stream=True)
        response.raise_for_status()
        set_weights(model, response.content)
    except Exception as e:
        print(f"[Sync Error] {e}")
        return {"error": str(e)}

# === Dataset ===
def load_uci_har_subject_data(subject_id, test_split=0.2):
    if not os.path.exists("UCI HAR Dataset/train/X_train.txt"):
        print("Dataset not available, downloading...")
        download_uci_har()  # Make sure this function is defined

    basepath = "UCI HAR Dataset/"
    X = np.loadtxt(basepath + "train/X_train.txt")
    y = np.loadtxt(basepath + "train/y_train.txt") - 1
    subjects = np.loadtxt(basepath + "train/subject_train.txt").astype(int)

    print(f"Loaded data for subject {subject_id}")
    mask = subjects == subject_id
    X_subj = X[mask]
    y_subj = y[mask]

    # Split: use the last N% as test set
    total_samples = len(X_subj)
    test_size = int(total_samples * test_split)
    train_size = total_samples - test_size

    X_train = X_subj[:train_size]
    y_train = y_subj[:train_size]
    X_test = X_subj[train_size:]
    y_test = y_subj[train_size:]

    print(f"Subject {subject_id}: train={X_train.shape[0]}, test={X_test.shape[0]}")
    return X_train, y_train, X_test, y_test

def download_uci_har():
    print("Downloading UCI HAR dataset...")
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00240/UCI%20HAR%20Dataset.zip"
    zip_path = os.curdir+"/uci_har.zip"
    urllib.request.urlretrieve(url, zip_path)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(".")
    print("Dataset downloaded and extracted.")