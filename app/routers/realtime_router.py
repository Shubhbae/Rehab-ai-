import base64
import json
import os
import numpy as np
from typing import Any, List, Dict, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from app.auth import get_current_user
from app.services.movenet_service import MoveNetService
from app.services.lstm_service import LSTMClassifier

router = APIRouter(prefix="/realtime", tags=["realtime"]) 

movenet = MoveNetService()
lstm = LSTMClassifier()


@router.websocket("/ws")
async def ws_realtime(websocket: WebSocket):
	await websocket.accept()
	poses_buffer = []
	try:
		while True:
			message = await websocket.receive_json()
			b64 = message.get("image_b64")
			if not b64:
				await websocket.send_json({"error": "missing image_b64"})
				continue

			# Handle base64 data URL format
			if ',' in b64:
				b64 = b64.split(',')[1]

			image_bytes = base64.b64decode(b64)
			# Convert bytes to numpy image
			import cv2
			nparr = np.frombuffer(image_bytes, np.uint8)
			frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

			if frame is None:
				await websocket.send_json({"error": "invalid image data"})
				continue

			poses = movenet.detect_keypoints(frame)
			poses_buffer.append(poses)
			if len(poses_buffer) >= 16:
				label, conf, dist = lstm.predict_sequence(poses_buffer[-16:])
				await websocket.send_json({"label": label, "confidence": conf})
	except WebSocketDisconnect:
		return

