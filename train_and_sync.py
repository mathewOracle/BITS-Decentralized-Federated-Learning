import numpy as np
import pickle
import tensorflow as tf
import requests, urllib
import os
import io
import zipfile
import fastapi
import json
import pandas as pd
import math
# os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# # === Model ===
def create_model(input_shape=561, num_classes=6):
    with tf.device('/CPU:0'):
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

def get_weights(model, param_type="None"):
    try:
        first_layer_weights, first_layer_biases = model.layers[0].get_weights()
        if param_type=="None":
            data = {'weights': first_layer_weights, 'biases': first_layer_biases}
        else:
            features_df = pd.read_excel("features.xls")
            filtered_indices = features_df[features_df['type'] == param_type]['No'].values - 1
            filtered_weights = first_layer_weights[filtered_indices, :]
            data = {'weights': filtered_weights, 'biases': first_layer_biases}
        data = pickle.dumps(data)
        return fastapi.responses.StreamingResponse(io.BytesIO(data), media_type="application/octet-stream")
    except Exception as e:
        raise RuntimeError(f"Error in get_weights: {e}")

def set_weights(model, data, param_type="None", alpha=0.8, location={"latitude": 0.0, "longitude": 0.0}):
    try:
        incoming = pickle.loads(data)
        current_weights = model.get_weights()
        first_layer_weights, first_layer_biases = current_weights[0], current_weights[1]

        if param_type=="None":
            averaged = alpha * incoming['weights'] + (1 - alpha) * first_layer_weights
            first_layer_weights = averaged
        else:
            features_df = pd.read_excel("features.xls")
            filtered_indices = features_df[features_df['type'] == param_type]['No'].values - 1
            if config_flag.get("enableTimeDistanceWeightage", False):
                distance = location_distance(location.latitude, location.longitude)
                print(f"Distance from peer: {distance} km")
                scale = 1000  # You can tune this value
                scaled_alpha = alpha * np.exp(-distance / scale)
            else:
                scaled_alpha = alpha
            averaged = scaled_alpha * incoming['weights'] + (1 - scaled_alpha) * first_layer_weights[filtered_indices, :]
            first_layer_weights[filtered_indices, :] = averaged

        current_weights[0] = first_layer_weights
        current_weights[1] = first_layer_biases
        model.set_weights(current_weights)
        return {"status": f"weights updated (averaged {param_type})", "layers": len(current_weights)}
    except Exception as e:
        return {"error": f"Error in set_weights: {e}"}

def gossip_sync(peer_url, model, param_type="None"):
    try:
        print(f"[Sync] Pulling weights from {peer_url}/weights")
        response = requests.get(f"http://{peer_url}/weights", params={'param_type':param_type}, stream=True)
        response.raise_for_status()
        set_weights(model, response.json()["weights"], param_type=param_type, location=response.json()["location"])
        print(f"[Sync] Weights set from peer {peer_url}")
    except Exception as e:
        print(f"[Sync Error] {e}")
        return {"error": str(e)}

# === Dataset ===

def load_uci_har_subject_data(subject_id=None, test_split=0.2):
    if not os.path.exists("UCI HAR Dataset/train/X_train.txt"):
        print("Dataset not available, downloading...")
        download_uci_har()  # Make sure this function is defined

    basepath = "UCI HAR Dataset/"
    X_train = np.loadtxt(basepath + "train/X_train.txt")
    y_train = np.loadtxt(basepath + "train/y_train.txt") - 1
    subjects_train = np.loadtxt(basepath + "train/subject_train.txt").astype(int)
    # Load test split
    X_test = np.loadtxt(basepath + "test/X_test.txt")
    y_test = np.loadtxt(basepath + "test/y_test.txt") - 1
    subjects_test = np.loadtxt(basepath + "test/subject_test.txt").astype(int)
    # Combine both
    X = np.concatenate([X_train, X_test], axis=0)
    y = np.concatenate([y_train, y_test], axis=0)
    subjects = np.concatenate([subjects_train, subjects_test], axis=0)

    if subject_id is None:
        X_subj = X
        y_subj = y
    else:
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

def getConfigMap(pod_index):
    config_file = f"/etc/feature-flags/flags-{pod_index}.json"
    try:
        with open(config_file) as f:
            flags = json.load(f)
    except FileNotFoundError:
        print(f"Feature flags file not found for pod {pod_index}, using default flags")
    try:    
        with open("/etc/feature-flags/default.json") as f:
                flags = json.load(f)
    except FileNotFoundError:
        print("Default feature flags file not found, using empty flags")
        flags = {}
    print(f"Pod {pod_index} using flags: {flags}")
    if flags.get("useSyncTraining"):
        print("Sync Federated Learning enabled")
    if flags.get("enableDeepShallowFeaturesweightage"):
        print("Deep Shallow Features weightage enabled")
    if flags.get("enableTimeDistanceWeightage"):
        print("Time Distance Weightage enabled")
    return flags

def location_distance(lat2, lon2):
    # Radius of Earth in kilometers
    R = 6371.0  
    # Convert decimal degrees to radians
    lat1_rad, lon1_rad = math.radians(LOCATION.latitude), math.radians(LOCATION.longitude)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

POD_NAME = os.getenv("HOSTNAME")
pod_index = POD_NAME.split("-")[-1]
config_flag = getConfigMap(pod_index) 
LOCATION = config_flag.get("location", {"latitude": 0.0, "longitude": 0.0})
print(f"Pod {pod_index} location: {LOCATION['latitude']}, {LOCATION['longitude']}"  )
print(f"Config flag: {config_flag}")