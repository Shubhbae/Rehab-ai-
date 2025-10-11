# backend/main.py - Remove camera access, only process frames sent from frontend

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import tensorflow as tf
import numpy as np
import cv2
import base64
from io import BytesIO
from PIL import Image
import os

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Load models
print("Loading models...")

# Import our existing services
import sys
sys.path.append('app')
from services.movenet_service import MoveNetService
from services.lstm_service import LSTMClassifier

# Load services
movenet_service = MoveNetService()
pose_classifier = LSTMClassifier()

# Load labels
with open('app/models/pose_labels.txt', 'r') as f:
    labels = [line.strip() for line in f.readlines()]

print(f"Models loaded. Classes: {labels}")

# ============================================
# REMOVE ANY cv2.VideoCapture() CODE
# Backend should NOT access camera directly
# ============================================

def base64_to_image(base64_string):
    """Convert base64 image from frontend to numpy array"""
    try:
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Decode base64
        image_bytes = base64.b64decode(base64_string)
        image = Image.open(BytesIO(image_bytes))
        image = np.array(image)
        
        # Convert RGB to BGR for OpenCV
        if len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        return image
    except Exception as e:
        print(f"Error decoding image: {e}")
        return None


def detect_keypoints(image):
    """Detect keypoints using MoveNet"""
    try:
        # Use our existing MoveNet service
        poses = movenet_service.detect_keypoints(image)
        return poses
    except Exception as e:
        print(f"Error detecting keypoints: {e}")
        return None


def classify_pose(keypoints):
    """Classify pose from keypoints"""
    try:
        # Use our existing LSTM service
        if len(keypoints) == 17:
            label, confidence, probs = pose_classifier.predict_sequence([keypoints])
            return {
                'pose': label,
                'confidence': confidence
            }
        else:
            return {
                'pose': 'unknown',
                'confidence': 0.0
            }
    except Exception as e:
        print(f"Error classifying pose: {e}")
        return None


def keypoints_to_list(keypoints):
    """Convert keypoints to list for JSON serialization"""
    if not keypoints or len(keypoints) == 0:
        return []
    
    return [
        {
            'x': float(kp.get('x', 0.0)),
            'y': float(kp.get('y', 0.0)),
            'score': float(kp.get('score', 0.0))
        }
        for kp in keypoints
    ]


# ============================================
# WebSocket endpoint for real-time streaming
# ============================================
@socketio.on('video_frame')
def handle_video_frame(data):
    """Process video frame from frontend"""
    try:
        # Get image data
        image_data = data.get('image')
        if not image_data:
            emit('error', {'message': 'No image data'})
            return
        
        # Convert to numpy array
        image = base64_to_image(image_data)
        if image is None:
            emit('error', {'message': 'Failed to decode image'})
            return
        
        # Detect keypoints
        keypoints = detect_keypoints(image)
        if keypoints is None:
            emit('error', {'message': 'Failed to detect keypoints'})
            return
        
        # Classify pose
        result = classify_pose(keypoints)
        if result is None:
            emit('error', {'message': 'Failed to classify pose'})
            return
        
        # Add keypoints for visualization
        result['keypoints'] = keypoints_to_list(keypoints)
        
        # Send back to frontend
        emit('pose_detected', result)
        
    except Exception as e:
        print(f"Error processing frame: {e}")
        emit('error', {'message': str(e)})


@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connected', {'message': 'Connected to pose detection server'})


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


# ============================================
# REST API endpoint (alternative to WebSocket)
# ============================================
@app.route('/api/detect-pose', methods=['POST'])
def detect_pose_api():
    """Process single frame via REST API"""
    try:
        data = request.json
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({'error': 'No image provided'}), 400
        
        # Convert to numpy array
        image = base64_to_image(image_data)
        if image is None:
            return jsonify({'error': 'Failed to decode image'}), 400
        
        # Detect keypoints
        keypoints = detect_keypoints(image)
        if keypoints is None:
            return jsonify({'error': 'Failed to detect keypoints'}), 500
        
        # Classify pose
        result = classify_pose(keypoints)
        if result is None:
            return jsonify({'error': 'Failed to classify pose'}), 500
        
        # Add keypoints
        result['keypoints'] = keypoints_to_list(keypoints)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"API error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'models_loaded': True,
        'classes': labels
    })


if __name__ == '__main__':
    print("\n" + "="*50)
    print("POSE DETECTION SERVER")
    print("="*50)
    print(f"Models: Loaded")
    print(f"Classes: {labels}")
    print(f"Server: http://localhost:5000")
    print("="*50 + "\n")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
