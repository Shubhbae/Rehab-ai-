#!/usr/bin/env python3
"""
Simple test script to verify H5 model and camera integration
"""
import cv2
import numpy as np
import base64
from app.services.lstm_service import LSTMClassifier
from app.services.movenet_service import MoveNetService

def test_h5_model():
    print("Testing H5 Model Loading...")
    try:
        lstm = LSTMClassifier()
        print("H5 Model loaded successfully!")
        
        # Test prediction
        test_poses = [[{'x': 0.5, 'y': 0.5, 'score': 0.9} for _ in range(17)]]
        label, conf, probs = lstm.predict_sequence(test_poses)
        print(f"Test prediction: {label} (confidence: {conf:.3f})")
        return True
    except Exception as e:
        print(f"H5 Model test failed: {e}")
        return False

def test_movenet():
    print("Testing MoveNet...")
    try:
        movenet = MoveNetService()
        print("MoveNet loaded successfully!")
        return True
    except Exception as e:
        print(f"MoveNet test failed: {e}")
        return False

def test_camera():
    print("Testing Camera Access...")
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Cannot open camera")
            return False
        
        ret, frame = cap.read()
        if not ret:
            print("Cannot read from camera")
            cap.release()
            return False
        
        print(f"Camera working! Frame shape: {frame.shape}")
        cap.release()
        return True
    except Exception as e:
        print(f"Camera test failed: {e}")
        return False

def test_full_pipeline():
    print("Testing Full Pipeline...")
    try:
        # Load services
        lstm = LSTMClassifier()
        movenet = MoveNetService()
        
        # Test camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Cannot open camera")
            return False
        
        print("Reading frame from camera...")
        ret, frame = cap.read()
        if not ret:
            print("Cannot read from camera")
            cap.release()
            return False
        
        print(f"Frame shape: {frame.shape}")
        
        # Test MoveNet
        print("Running MoveNet detection...")
        poses = movenet.detect_keypoints(frame)
        print(f"Detected {len(poses)} keypoints")
        
        if len(poses) > 0:
            print(f"First keypoint: {poses[0]}")
        
        # Test LSTM
        if len(poses) == 17:
            print("Running LSTM prediction...")
            label, conf, probs = lstm.predict_sequence([poses])
            print(f"Prediction: {label} (confidence: {conf:.3f})")
            print("Full pipeline working!")
        else:
            print(f"Not enough keypoints for prediction: {len(poses)}/17")
        
        cap.release()
        return True
        
    except Exception as e:
        print(f"Full pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting Camera + H5 Model Tests...")
    print("=" * 50)
    
    # Test individual components
    h5_ok = test_h5_model()
    movenet_ok = test_movenet()
    camera_ok = test_camera()
    
    print("\n" + "=" * 50)
    
    if h5_ok and movenet_ok and camera_ok:
        print("All components working! Testing full pipeline...")
        test_full_pipeline()
    else:
        print("Some components failed. Please fix the issues above.")
    
    print("\n" + "=" * 50)
    print("Test completed!")
