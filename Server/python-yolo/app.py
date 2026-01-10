# app.py
from fastapi import FastAPI, Request
from ultralytics import YOLO
from PIL import Image
import io

app = FastAPI()
model = YOLO("./best_models/best_1.pt")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/infer")
async def infer(request: Request):
    img_bytes = await request.body()
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    results = model.predict(img, verbose=False)

    dets = []
    r = results[0]
    names = r.names  # словарь id->label

    if r.boxes is not None:
        for b in r.boxes:
            cls_id = int(b.cls[0].item())
            conf = float(b.conf[0].item())
            x1, y1, x2, y2 = [int(v) for v in b.xyxy[0].tolist()]

            dets.append({
                "clazz": names[cls_id],
                "confidence": conf,
                "bbox": {"xMin": x1, "yMin": y1, "xMax": x2, "yMax": y2}
            })

    return {"detections": dets}
