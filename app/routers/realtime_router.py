import base64
import json
import os
import numpy as np
import cv2
from typing import Any, List, Dict, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from pydantic import BaseModel
from PIL import Image
from io import BytesIO

from app.auth import get_current_user
from app.services.movenet_service import MoveNetService
from app.services.lstm_service import LSTMClassifier

router = APIRouter(prefix="/realtime", tags=["realtime"]) 

movenet = MoveNetService()
lstm = LSTMClassifier()

def preprocess_image(image_data: str):
    """Convert base64 image to tensor for MoveNet - improved from Flask code"""
    try:
        # Handle base64 data URL format
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Decode base64
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        image = np.array(image)
        
        # Convert BGR to RGB if needed
        if len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Resize to 256x256 for MoveNet Thunder
        image = cv2.resize(image, (256, 256))
        
        return image
    except Exception as e:
        print(f"[REALTIME] Image preprocessing error: {e}")
        return None

def keypoints_to_dict(keypoints: np.ndarray) -> List[Dict]:
    """Convert keypoints array to list of dicts for frontend - from Flask code"""
    if keypoints is None or len(keypoints) == 0:
        return []
    
    return [
        {
            'x': float(kp[1]),  # MoveNet returns [y, x, score]
            'y': float(kp[0]),
            'score': float(kp[2])
        }
        for kp in keypoints
    ]

class ImageRequest(BaseModel):
    image: str

@router.get("/test")
async def test_realtime():
	return {"status": "realtime service is working", "movenet": "loaded", "lstm": "loaded"}

@router.post("/detect-pose")
async def detect_pose(request: ImageRequest):
    """Process single frame and return pose detection - from Flask code"""
    try:
        image_data = request.image
        
        if not image_data:
            raise HTTPException(status_code=400, detail="No image provided")
        
        # Process image using improved preprocessing
        frame = preprocess_image(image_data)
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image data")
        
        # Detect keypoints
        poses = movenet.detect_keypoints(frame)
        
        # Convert keypoints to dict format
        keypoints_dict = keypoints_to_dict(poses)
        
        # Classify pose
        if len(poses) == 17:
            label, conf, dist = lstm.predict_sequence([poses])
            result = {
                "pose": label,
                "confidence": float(conf),
                "all_probabilities": dist,
                "keypoints": keypoints_dict,
                "frame_shape": [frame.shape[1], frame.shape[0]]
            }
        else:
            result = {
                "pose": "unknown",
                "confidence": 0.0,
                "all_probabilities": [0.2, 0.2, 0.2, 0.2, 0.2],
                "keypoints": keypoints_dict,
                "frame_shape": [frame.shape[1], frame.shape[0]]
            }
        
        return result
        
    except Exception as e:
        print(f"[REALTIME] Error in detect-pose: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws")
async def ws_realtime(websocket: WebSocket):
	await websocket.accept()
	print("[REALTIME] WebSocket connection established!")
	poses_buffer = []
	try:
		while True:
			message = await websocket.receive_json()
			print(f"[REALTIME] Received message: {list(message.keys())}")
			image_data = message.get("image_b64")
			if not image_data:
				await websocket.send_json({"error": "missing image_b64"})
				continue

			# Use improved preprocessing from Flask code
			frame = preprocess_image(image_data)
			if frame is None:
				await websocket.send_json({"error": "invalid image data"})
				continue

			# Get keypoints from MoveNet
			poses = movenet.detect_keypoints(frame)
			poses_buffer.append(poses)
			
			# Debug: Print keypoints info
			print(f"[REALTIME] Detected {len(poses)} keypoints")
			if len(poses) > 0:
				print(f"[REALTIME] First keypoint: {poses[0]}")
			
			# Convert keypoints to dict format for frontend
			keypoints_dict = keypoints_to_dict(poses)
			
			# Send keypoints for skeleton visualization
			response = {
				"keypoints": keypoints_dict,
				"frame_shape": [frame.shape[1], frame.shape[0]]  # [width, height]
			}
			
			# Add LSTM prediction for single-frame model
			if len(poses) == 17:  # Valid keypoints detected
				label, conf, dist = lstm.predict_sequence([poses])  # Single frame
				print(f"[REALTIME] LSTM Prediction: {label} (confidence: {conf:.3f})")
				response.update({
					"label": label, 
					"confidence": conf,
					"prediction_available": True,
					"all_probabilities": dist
				})
			else:
				print(f"[REALTIME] Not enough keypoints for prediction: {len(poses)}/17")
				response.update({
					"prediction_available": False,
					"frames_needed": 0
				})
			
			await websocket.send_json(response)
	except WebSocketDisconnect:
		return

