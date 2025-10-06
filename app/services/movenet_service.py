import os
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import cv2
from typing import List, Dict, Tuple, Optional

from app.config import settings


class MoveNetService:
	def __init__(self):
		self.model = hub.load(settings.movenet_model_handle)

	def _resize_and_pad(self, image: np.ndarray, target_size: Tuple[int, int] = (256, 256)) -> np.ndarray:
		img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
		img = tf.image.resize_with_pad(img, target_size[0], target_size[1])
		img = tf.cast(img, dtype=tf.int32)
		return img.numpy()

	def detect_keypoints(self, frame: np.ndarray) -> List[Dict]:
		try:
			if frame is None:
				return []
			input_image = self._resize_and_pad(frame)
			input_tensor = tf.expand_dims(input_image, axis=0)
			outputs = self.model.signatures['serving_default'](input_tensor)
			keypoints_with_scores = outputs['output_0'].numpy()  # [1,1,17,3]
			kps = keypoints_with_scores[0, 0, :, :]
			result = []
			for kp in kps:
				y, x, score = kp
				result.append({"x": float(x), "y": float(y), "score": float(score)})
			return result
		except Exception as e:
			print(f"MoveNet error: {e}")
			return []

	def process_video(self, video_path: str, stride: int = 1) -> List[List[Dict]]:
		cap = cv2.VideoCapture(video_path)
		poses: List[List[Dict]] = []
		frame_index = 0
		while True:
			ret, frame = cap.read()
			if not ret:
				break
			if frame_index % stride == 0:
				poses.append(self.detect_keypoints(frame))
			frame_index += 1
		cap.release()
		return poses

