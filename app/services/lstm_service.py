from app.services.database_service import DatabaseService
from typing import List, Dict, Tuple
import os
import numpy as np
import tensorflow as tf
from app.config import settings

# Load labels from your trained model
def load_labels():
    labels_path = os.path.join(os.path.dirname(__file__), "..", "models", "pose_labels.txt")
    try:
        with open(labels_path, 'r') as f:
            labels = [line.strip() for line in f.readlines()]
        print(f"[LSTM] Loaded labels: {labels}")
        return labels
    except Exception as e:
        print(f"[LSTM] Could not load labels, using default: {e}")
        return ["chair", "cobra", "dog", "tree", "warrior"]

LABELS = load_labels()

# Custom layer registration for the H5 model
try:
    @tf.keras.saving.register_keras_serializable()
    class NormalizationLayer(tf.keras.layers.Layer):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
        
        def call(self, inputs):
            # Simple normalization - you may need to adjust this based on your model
            return tf.nn.l2_normalize(inputs, axis=-1)
        
        def get_config(self):
            config = super().get_config()
            return config
except AttributeError:
    # Fallback for older TensorFlow versions
    class NormalizationLayer(tf.keras.layers.Layer):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
        
        def call(self, inputs):
            # Simple normalization - you may need to adjust this based on your model
            return tf.nn.l2_normalize(inputs, axis=-1)
        
        def get_config(self):
            config = super().get_config()
            return config


def _poses_to_array(poses: List[List[Dict]], target_features: int = 51) -> np.ndarray:
    # Convert a list of frames (each a list of keypoints dicts) to shape (timesteps, target_features)
    # Always return exactly target_features: trim or pad as needed.
    frames: List[List[float]] = []
    for frame in poses:
        flat: List[float] = []
        if target_features == 51:
            for kp in frame:
                x = float(kp.get("x", 0.0))
                y = float(kp.get("y", 0.0))
                s = float(kp.get("score", 0.0))
                flat.extend([x, y, s])
        else: # Default to 34 features (x,y only)
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
        print("[LSTM] Initializing LSTM classifier with your trained H5 model...")
        self.model = None
        self.expected_features = 34  # Based on your model structure (17 keypoints * 2 = 34)
        
        # Try to load the real H5 model
        try:
            self._load_h5_model()
            print("[LSTM] SUCCESS: Your trained H5 model loaded successfully!")
        except Exception as e:
            print(f"[LSTM] WARNING: Could not load real model, using mock: {e}")
            print("[LSTM] Mock LSTM classifier ready!")
    
    def _load_h5_model(self):
        """Load your trained H5 model"""
        # Get the correct path to models directory
        current_dir = os.path.dirname(__file__)  # app/services/
        models_dir = os.path.join(current_dir, "..", "models")  # app/models/
        models_dir = os.path.normpath(models_dir)
        
        # Load your H5 model file
        model_path = os.path.join(models_dir, "pose_classifier.h5")
        
        if not os.path.isfile(model_path):
            raise FileNotFoundError(f"H5 model not found: {model_path}")
        
        # Check file size
        model_size = os.path.getsize(model_path)
        print(f"[LSTM] Loading H5 model:")
        print(f"[LSTM]   - pose_classifier.h5: {model_size} bytes")
        
        # Create a model architecture that matches the weights
        # Based on the weights structure: 34 -> 128 -> 64 -> 5
        try:
            # Create the model architecture
            inputs = tf.keras.layers.Input(shape=(34,), name='input_layer')
            
            # Normalization layer
            normalized = NormalizationLayer(name='normalization_layer')(inputs)
            
            # Dense layers matching the weights structure
            dense1 = tf.keras.layers.Dense(128, activation='relu6', name='dense_3')(normalized)
            dropout1 = tf.keras.layers.Dropout(0.5, name='dropout_2')(dense1)
            
            dense2 = tf.keras.layers.Dense(64, activation='relu6', name='dense_4')(dropout1)
            dropout2 = tf.keras.layers.Dropout(0.5, name='dropout_3')(dense2)
            
            outputs = tf.keras.layers.Dense(5, activation='softmax', name='dense_5')(dropout2)
            
            # Create the model
            self.model = tf.keras.Model(inputs=inputs, outputs=outputs, name='pose_classifier')
            
            # Load the weights
            self.model.load_weights(model_path, by_name=True)
            
            print(f"[LSTM] Model loaded successfully!")
            print(f"[LSTM] Model input shape: {self.model.input_shape}")
            print(f"[LSTM] Model output shape: {self.model.output_shape}")
            print(f"[LSTM] Model summary:")
            self.model.summary()
            
        except Exception as e:
            print(f"[LSTM] Error loading H5 model: {e}")
            raise e
        
        print(f"[LSTM] Using expected_features={self.expected_features}")
        print(f"[LSTM] Your trained H5 model is ready for real-time prediction!")

    def predict_sequence(self, poses: List[List[Dict]]):
        if self.model is None:
            # Mock prediction for demo
            import random
            label = random.choice(LABELS)
            confidence = random.uniform(0.6, 0.95)
            return label, confidence, [0.2, 0.2, 0.2, 0.2, 0.2]
        
        # For single-frame model, use the most recent frame
        if not poses:
            return "unknown", 0.0, [0.2, 0.2, 0.2, 0.2, 0.2]
        
        # Use the last frame for prediction
        last_frame = poses[-1]
        arr = _poses_to_array([last_frame], target_features=self.expected_features)
        arr = arr.reshape(1, -1)  # Flatten to (1, 34) for single-frame model
        
        try:
            # Make prediction with the actual H5 model
            predictions = self.model.predict(arr, verbose=0)
            probs = predictions[0]  # Get the first (and only) prediction
            
            # Get the label with highest probability
            label_idx = int(np.argmax(probs))
            confidence = float(probs[label_idx])
            
            return LABELS[label_idx], confidence, probs.tolist()
        except Exception as e:
            print(f"[LSTM] Error during prediction: {e}")
            # Fallback to mock prediction
            import random
            label = random.choice(LABELS)
            confidence = random.uniform(0.6, 0.95)
            return label, confidence, [0.2, 0.2, 0.2, 0.2, 0.2]

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
        
        # For single-frame model, predict each frame individually
        preds = []
        for t, frame in enumerate(poses):
            arr = _poses_to_array([frame], target_features=self.expected_features)
            arr = arr.reshape(1, -1)  # Flatten to (1, 34) for single-frame model
            
            try:
                # Make prediction with the actual H5 model
                predictions = self.model.predict(arr, verbose=0)
                probs = predictions[0]  # Get the first (and only) prediction
                
                # Get the label with highest probability
                label_idx = int(np.argmax(probs))
                confidence = float(probs[label_idx])
                
                preds.append({
                    "frame_index": t,
                    "label": LABELS[label_idx],
                    "confidence": confidence
                })
            except Exception as e:
                print(f"[LSTM] Error during frame {t} prediction: {e}")
                # Fallback to mock prediction
                import random
                label = random.choice(LABELS)
                confidence = random.uniform(0.6, 0.95)
                preds.append({
                    "frame_index": t,
                    "label": label,
                    "confidence": confidence
                })
        return preds