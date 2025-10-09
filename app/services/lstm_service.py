from typing import List, Dict, Tuple
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
		# Prefer a .keras model if present in the models directory; otherwise fall back to configured path
		models_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", settings.models_dir))
		keras_candidates = [
			os.path.join(models_dir, "weights.best.keras"),
			os.path.join(models_dir, "lstm_model.keras"),
		]
		print("[LSTM] 🔍 Searching for model file...")
		print(f"[LSTM] 📁 Models directory: {models_dir}")
		for c in keras_candidates:
			exists = os.path.isfile(c)
			size_info = f", size={os.path.getsize(c)} bytes" if exists else ""
			print(f"[LSTM] ▶ Candidate: {c} | exists={exists}{size_info}")

		model_path = None
		for candidate in keras_candidates:
			if os.path.isfile(candidate):
				model_path = candidate
				break
		if model_path is None:
			# Fall back to the configured path (may be .h5 or .keras)
			model_path = settings.lstm_model_path
		print(f"[LSTM] 🧭 Selected model path: {model_path}")

		if not os.path.isfile(model_path):
			print(f"[LSTM] ❌ Model file NOT found at: {model_path}")
			print(f"[LSTM] ❌ CWD: {os.getcwd()}")
			models_dir_exists = os.path.isdir(models_dir)
			print(f"[LSTM] ❌ models_dir exists: {models_dir_exists}")
			try:
				listing = os.listdir(models_dir) if models_dir_exists else []
				print(f"[LSTM] ❌ Files in models_dir: {listing}")
			except Exception as e:
				print(f"[LSTM] ❌ Could not list models_dir: {e}")
			# Still attempt load to raise informative error
		
		try:
			print("[LSTM] ⏳ Loading model...")
			self.model = tf.keras.models.load_model(model_path)
			print("[LSTM] ✅ Model loaded successfully!")
			try:
				print(f"[LSTM] ✅ Input shape: {getattr(self.model, 'input_shape', 'unknown')}")
				print(f"[LSTM] ✅ Output shape: {getattr(self.model, 'output_shape', 'unknown')}")
				print(f"[LSTM] ✅ Layers: {len(getattr(self.model, 'layers', []))}")
			except Exception:
				pass
		except Exception as e:
			print(f"[LSTM] ❌ Error loading model: {e}")
			raise

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

