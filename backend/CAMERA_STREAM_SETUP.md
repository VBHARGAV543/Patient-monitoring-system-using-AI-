# Camera Stream Endpoint - Backend Addition for Phase 4

## Required Backend Change (Minimal)

Add this endpoint to `backend/main.py` to serve laptop webcam stream:

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import cv2

# Add to existing main.py

@app.get("/stream")
async def video_stream():
    """
    MJPEG video stream from laptop webcam.
    Mobile app will display this stream when viewing alerted patients.
    """
    def generate():
        camera = cv2.VideoCapture(0)  # Laptop webcam
        try:
            while True:
                success, frame = camera.read()
                if not success:
                    break
                
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                
                # MJPEG format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        finally:
            camera.release()
    
    return StreamingResponse(
        generate(),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )
```

## Requirements

```bash
pip install opencv-python
```

## Testing

1. Start backend: `uvicorn main:app --host 0.0.0.0 --port 8000`
2. Open browser: `http://localhost:8000/stream`
3. Should see live webcam feed

## Mobile App Configuration

Mobile app connects to: `http://<BACKEND_IP>:8000/stream`

The stream URL is currently hardcoded in `CameraStreamActivity.kt` but will be configurable in Phase 2.
