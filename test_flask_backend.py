#!/usr/bin/env python3
"""
Test script to verify Flask backend works
"""
import sys
import os

def test_imports():
    print("Testing imports...")
    try:
        import flask
        print("Flask available")
    except ImportError:
        print("Flask not available - install with: pip install flask")
        return False
    
    try:
        import flask_cors
        print("Flask-CORS available")
    except ImportError:
        print("Flask-CORS not available - install with: pip install flask-cors")
        return False
    
    try:
        import flask_socketio
        print("Flask-SocketIO available")
    except ImportError:
        print("Flask-SocketIO not available - install with: pip install flask-socketio")
        return False
    
    try:
        import tensorflow as tf
        print("TensorFlow available")
    except ImportError:
        print("TensorFlow not available")
        return False
    
    try:
        import cv2
        print("OpenCV available")
    except ImportError:
        print("OpenCV not available")
        return False
    
    try:
        from PIL import Image
        print("PIL available")
    except ImportError:
        print("PIL not available")
        return False
    
    return True

def test_models():
    print("\nTesting model loading...")
    try:
        import tensorflow as tf
        
        # Test MoveNet loading
        print("Loading MoveNet...")
        movenet = tf.saved_model.load('https://tfhub.dev/google/movenet/singlepose/thunder/4')
        print("MoveNet loaded successfully")
        
        # Test H5 model loading
        print("Loading H5 model...")
        h5_path = 'app/models/pose_classifier.h5'
        if os.path.exists(h5_path):
            pose_classifier = tf.keras.models.load_model(h5_path, compile=False)
            print("H5 model loaded successfully")
        else:
            print(f"H5 model not found at {h5_path}")
            return False
        
        # Test labels loading
        labels_path = 'app/models/pose_labels.txt'
        if os.path.exists(labels_path):
            with open(labels_path, 'r') as f:
                labels = [line.strip() for line in f.readlines()]
            print(f"Labels loaded: {labels}")
        else:
            print(f"Labels not found at {labels_path}")
            return False
        
        return True
        
    except Exception as e:
        print(f"Model loading failed: {e}")
        return False

def main():
    print("=" * 50)
    print("FLASK BACKEND TEST")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("\nImport test failed. Install missing packages:")
        print("pip install flask flask-cors flask-socketio")
        return
    
    # Test models
    if not test_models():
        print("\nModel test failed.")
        return
    
    print("\nAll tests passed!")
    print("\nTo run the Flask backend:")
    print("python flask_backend.py")
    print("\nThe backend will run on http://localhost:8000")
    print("Frontend should connect to this URL for pose detection")

if __name__ == "__main__":
    main()
