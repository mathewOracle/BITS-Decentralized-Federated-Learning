from fastapi import FastAPI, Response
from pydantic import BaseModel
import numpy as np
import os
from train_and_sync import create_model, train_model, get_weights, set_weights, gossip_sync
from apscheduler.schedulers.background import BackgroundScheduler


app = FastAPI()
model = create_model()
last_loss = 0.0
last_mse = 0.0
scheduler = BackgroundScheduler()

class SyncRequest(BaseModel):
    peer: str

def train():
    print("Training model...")
    global last_loss
    try:
        x = np.random.rand(50, 1)
        y = 2 * x + 1 + np.random.randn(50, 1) * 0.1
        _, loss = train_model(x, y, model)
        last_loss = loss
        return {"status": "trained", "loss": loss}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
    
def evaluate():
    print("Evaluating model...")
    global last_mse
    x_test = np.linspace(0, 1, 20).reshape(-1, 1)
    y_true = 2 * x_test + 1
    y_pred = model.predict(x_test)
    mse = np.mean((y_true - y_pred) ** 2)
    last_mse = float(mse)
    return {"mse": last_mse}
    
@app.post("/train")
def trigger_train():
    return train()

@app.get("/evaluate")
def trigger_evaluate():
    return evaluate()

@app.on_event("startup")
def startup_event():
    scheduler.add_job(train, 'interval', seconds=10)
    scheduler.add_job(evaluate, 'interval', seconds=10)
    scheduler.add_job(sync_all, 'interval', seconds=30)
    scheduler.start()

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
    print("Peers to sync with:", peers)
    for peer in peers:
        if peer:
            gossip_sync(peer.strip(), model)
    return {"status": "gossip sync done"}

@app.get("/metrics")
def metrics():
    print(f"ml_loss {last_loss}\nml_mse {last_mse}")
    return Response(
        content=f"ml_loss {last_loss}\nml_mse {last_mse}\n",
        media_type="text/plain"
    )