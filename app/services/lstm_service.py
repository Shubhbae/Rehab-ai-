from app.services.database_service import DatabaseService
from typing import List, Dict, Tuple
import os
import numpy as np
import tensorflow as tf
from app.config import settings

# Updated labels for 5 yoga poses
LABELS = ["mountain_pose", "warrior_1", "warrior_2", "tree_pose", "downward_dog"]

# Custom layer registration for the new model
class NormalizationLayer(tf.keras.layers.Layer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def call(self, inputs):
        # Simple normalization - you may need to adjust this based on your model
        return tf.nn.l2_normalize(inputs, axis=-1)
    
    def get_config(self):
        config = super().get_config()
        return config


def _poses_to_array(poses: List[List[Dict]], target_features: int = 34) -> np.ndarray:
    # Convert a list of frames (each a list of keypoints dicts) to shape (timesteps, 34)
    # Always return exactly 34 features (x,y for 17 points): trim or pad as needed.
    frames: List[List[float]] = []
    for frame in poses:
        flat: List[float] = []
        if target_features == 51:
            for kp in frame:
                x = float(kp.get("x", 0.0))
                y = float(kp.get("y", 0.0))
                s = float(kp.get("score", 0.0))
                flat.extend([x, y, s])
        else:
            for kp in frame:
                x = float(kp.get("x", 0.0))
                y = float(kp.get("y", 0.0))
                flat.extend([x, y])
        # Ensure exact feature length
        if len(flat) > target_features:
            flat = flat[:target_features]
        elif len(flat) < target_features:
            flat.extend([0.0] * (target_features - len(flat)))
        frames.append(flat)
    if not frames:
        frames.append([0.0] * target_features)
    return np.asarray(frames, dtype=np.float32)


class LSTMClassifier:
	def __init__(self):
		print("[LSTM] Initializing mock LSTM classifier...")
		self.model = None
		print("[LSTM] Mock LSTM classifier ready!")
		
		# Try to load the real model in the background
		try:
			self._load_real_model()
		except Exception as e:
			print(f"[LSTM] Could not load real model, using mock: {e}")
		self.expected_features = 34
	
	def _load_real_model(self):
		"""Try to load the real model - can be called later"""
		models_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", settings.models_dir))
		keras_candidates = [
			os.path.join(models_dir, "weights.best.keras"),
			os.path.join(models_dir, "lstm_model.keras"),
		]
		
		model_path = None
		for candidate in keras_candidates:
			if os.path.isfile(candidate):
				model_path = candidate
				break
		if model_path is None:
			model_path = settings.lstm_model_path
		
		if os.path.isfile(model_path):
			print("[LSTM] Attempting to load real model...")
			custom_objects = {'NormalizationLayer': NormalizationLayer}
			try:
				self.model = tf.keras.models.load_model(
					model_path,
					custom_objects=custom_objects,
					compile=False,
					safe_mode=False,
				)
				print("[LSTM] Real model loaded successfully!")
				# Infer expected feature size from model input
				try:
					shape = self.model.input_shape
					print(f"[LSTM] Model input_shape: {shape}")
					if isinstance(shape, (list, tuple)):
						self.expected_features = int(shape[-1]) if shape[-1] else 34
					print(f"[LSTM] Using expected_features={self.expected_features}")
				except Exception:
					self.expected_features = 34
			except Exception as e:
				print(f"[LSTM] Failed to load real model: {e}")
				raise

	def predict_sequence(self, poses: List[List[Dict]]):
		if self.model is None:
			# Mock prediction for demo
			import random
			label = random.choice(LABELS)
			confidence = random.uniform(0.6, 0.95)
			return label, confidence, [0.2, 0.2, 0.2, 0.2, 0.2]
		
		arr = _poses_to_array(poses, target_features=getattr(self, 'expected_features', 34))
		arr = np.expand_dims(arr, axis=0)  # (1, timesteps, features)
		probs = self.model.predict(arr, verbose=0)[0]  # assume (timesteps or 1, num_classes)
		if probs.ndim == 2:  # if returns per-timestep, take mean
			probs = probs.mean(axis=0)
		label_idx = int(np.argmax(probs))
		return LABELS[label_idx], float(probs[label_idx]), probs.tolist()

	def predict_per_frame(self, poses: List[List[Dict]]):
		if self.model is None:
			# Mock prediction for demo
			import random
			preds = []
			for t in range(len(poses)):
				label = random.choice(LABELS)
				confidence = random.uniform(0.6, 0.95)
				preds.append({
					"frame_index": t,
					"label": label,
					"confidence": confidence
				})
			return preds
		
		arr = _poses_to_array(poses, target_features=getattr(self, 'expected_features', 34))
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

