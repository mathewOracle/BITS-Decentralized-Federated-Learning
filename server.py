from fastapi import FastAPI, Response
from pydantic import BaseModel
import numpy as np
import os
from train_and_sync import create_model, train_model, get_weights, set_weights, gossip_sync

app = FastAPI()
model = create_model()
last_loss = 0.0
last_mse = 0.0

class SyncRequest(BaseModel):
    peer: str

@app.post("/train")
def train():
    global last_loss
    x = np.random.rand(50, 1)
    y = 2 * x + 1 + np.random.randn(50, 1) * 0.1
    _, loss = train_model(x, y, model)
    last_loss = loss
    return {"status": "trained", "loss": loss}

@app.get("/weights")
def weights():
    return get_weights(model)

@app.post("/sync")
def sync(req: SyncRequest):
    gossip_sync(req.peer, model)
    return {"status": f"synced with {req.peer}"}

@app.post("/sync-all")
def sync_all():
    peers = os.environ.get("PEERS", "").split(',')
    for peer in peers:
        if peer:
            gossip_sync(peer.strip(), model)
    return {"status": "gossip sync done"}

@app.get("/evaluate")
def evaluate():
    global last_mse
    x_test = np.linspace(0, 1, 20).reshape(-1, 1)
    y_true = 2 * x_test + 1
    y_pred = model.predict(x_test)
    mse = np.mean((y_true - y_pred) ** 2)
    last_mse = float(mse)
    return {"mse": last_mse}

@app.get("/metrics")
def metrics():
    return Response(
        content=f"ml_loss {last_loss}\nml_mse {last_mse}\n",
        media_type="text/plain"
    )