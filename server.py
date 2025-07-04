from fastapi import FastAPI, Response
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
from prometheus_client import Gauge, Counter, generate_latest, CONTENT_TYPE_LATEST
import numpy as np
import os
import time

from train_and_sync import (
    create_model,
    train_model,
    get_weights,
    set_weights,
    gossip_sync,
    load_uci_har_subject_data,
)

# Environment Setup
POD_NAME = os.getenv("HOSTNAME")
POD_IP = os.popen("hostname -i").read().strip()
SUBJECT_ID = int(os.environ.get("SUBJECT_ID", "1"))
PEERS = os.environ.get("PEERS", "").split(",")
print(f"POD_NAME: {POD_NAME}, POD_IP: {POD_IP}, SUBJECT_ID: {SUBJECT_ID}, PEERS: {PEERS}")

app = FastAPI()
model = create_model(input_shape=561, num_classes=6)
scheduler = BackgroundScheduler()

# Metrics
loss_metric = Gauge("har_training_loss", "Training loss on UCI HAR",["stage"])
acc_metric = Gauge("har_training_accuracy", "Training accuracy on UCI HAR",["stage"])
mse_metric = Gauge("har_eval_mse", "Evaluation MSE on same-subject data",["stage"])
sync_counter = Counter("har_sync_count", "Number of successful peer syncs")

# Internal state
last_loss = 0.0
last_acc = 0.0
last_mse = 0.0

stream_index = 0
stream_batch_size = 10
X_stream = None
y_stream = None

class SyncRequest(BaseModel):
    peer: str

def train(sync_stage):
    global last_loss, last_acc, stream_index, X_stream, y_stream
    try:
        if X_stream is None or y_stream is None:
            X_stream, y_stream = load_uci_har_subject_data(SUBJECT_ID)
            print(f"[Init] Subject {SUBJECT_ID}: {X_stream.shape[0]} samples")

        if stream_index >= len(X_stream):
            print("End of data stream reached. Restarting stream.")
            stream_index = 0

        # Get current batch
        end = min(stream_index + stream_batch_size, len(X_stream))
        X_batch = X_stream[stream_index:end]
        y_batch = y_stream[stream_index:end]
        
        # Train on batch
        _, loss, acc = train_model(X_batch, y_batch, model, epochs=1)
        last_loss = float(loss)
        last_acc = float(acc)
        loss_metric.labels(stage=sync_stage).set(last_loss)
        acc_metric.labels(stage=sync_stage).set(last_acc)
        stream_index = end  # move pointer
        
        print(f"[{sync_stage} Train] Trained on batch {stream_index - stream_batch_size} to {end} | Loss={loss:.4f} Acc={acc:.4f}")
        
        return {"status": "trained", "batch": f"{stream_index - stream_batch_size}-{end}", "post sync loss": loss, "post sync acc": acc}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


def evaluate(sync_stage):
    global last_mse
    try:
        X_eval = X_stream
        y_eval = y_stream

        preds = model.predict(X_eval)
        pred_labels = np.argmax(preds, axis=1)
        mse = np.mean((pred_labels - y_eval) ** 2)

        last_mse = float(mse)
        mse_metric.labels(stage=sync_stage).set(last_mse)

        print(f"[{sync_stage} Eval] Evaluated for the subject whole data | MSE={mse:.4f}")
        return {"mse": mse}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


def process():
    train("pre-sync")
    evaluate("pre-sync")
    sync_all()
    train("post-sync")
    evaluate("post-sync")

@app.post("/train")
def trigger_train():
    return train("maunal-trigger")

@app.get("/evaluate")
def trigger_evaluate():
    return evaluate("maunal-trigger")

@app.get("/weights")
def get_model_weights():
    model_weights=get_weights(model)
    print("Model Weights: {model_weights}")
    return model_weights

@app.post("/sync")
def sync(req: SyncRequest):
    gossip_sync(req.peer, model)
    sync_counter.inc()
    return {"status": f"synced with {req.peer}"}

@app.post("/sync-all")
def sync_all():
    for peer in PEERS:
        if peer.strip():
            gossip_sync(peer.strip(), model)
            sync_counter.inc()
    return {"status": "synced with all peers"}

@app.get("/metrics")
def prometheus_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.on_event("startup")
def startup_event():
    scheduler.add_job(process, "interval", seconds=15)
    scheduler.start()
