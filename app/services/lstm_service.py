from typing import List, Dict, Tuple, Optional
import os
import numpy as np
import tensorflow as tf
from app.config import settings

LABELS = ["squat", "step_jack", "half_wheel"]


def _poses_to_array(poses: List[List[Dict]]) -> np.ndarray:
	# poses: list of frames; each frame is list of keypoint dicts with x,y,score
	# Convert to shape (timesteps, 17*3)
	frames = []
	for frame in poses:
		flat = []
		for kp in frame:
			flat.extend([kp.get("x", 0.0), kp.get("y", 0.0), kp.get("score", 0.0)])
		frames.append(flat)
	return np.array(frames, dtype=np.float32)


class LSTMClassifier:
	def __init__(self):
		if not os.path.exists(settings.lstm_model_path):
			raise FileNotFoundError(f"LSTM model not found at {settings.lstm_model_path}")
		self.model = tf.keras.models.load_model(settings.lstm_model_path)

	def predict_sequence(self, poses: List[List[Dict]]):
		arr = _poses_to_array(poses)
		arr = np.expand_dims(arr, axis=0)  # (1, timesteps, features)
		probs = self.model.predict(arr, verbose=0)[0]  # assume (timesteps or 1, num_classes)
		if probs.ndim == 2:  # if returns per-timestep, take mean
			probs = probs.mean(axis=0)
		label_idx = int(np.argmax(probs))
		return LABELS[label_idx], float(probs[label_idx]), probs.tolist()

	def predict_per_frame(self, poses: List[List[Dict]]):
		arr = _poses_to_array(poses)
		arr = np.expand_dims(arr, axis=0)
		probs = self.model.predict(arr, verbose=0)
		if probs.ndim == 3:
			probs = probs[0]
		preds = []
		for t in range(probs.shape[0]):
			label_idx = int(np.argmax(probs[t]))
			preds.append({
				"frame_index": t,
				"label": LABELS[label_idx],
				"confidence": float(probs[t][label_idx])
			})
		return preds

