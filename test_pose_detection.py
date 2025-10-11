#!/usr/bin/env python3
"""
Test pose detection with Flask backend
"""
import requests
import base64
import numpy as np
import cv2
import json

def create_test_image():
    """Create a simple test image"""
    # Create a 480x640 test image with a simple pattern
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add some colored rectangles to simulate a person
    cv2.rectangle(img, (200, 100), (400, 400), (100, 150, 200), -1)  # Body
    cv2.circle(img, (300, 80), 30, (200, 180, 160), -1)  # Head
    cv2.rectangle(img, (150, 200), (200, 350), (100, 150, 200), -1)  # Left arm
    cv2.rectangle(img, (400, 200), (450, 350), (100, 150, 200), -1)  # Right arm
    cv2.rectangle(img, (250, 400), (300, 480), (100, 150, 200), -1)  # Left leg
    cv2.rectangle(img, (300, 400), (350, 480), (100, 150, 200), -1)  # Right leg
    
    return img

def test_pose_detection():
    """Test pose detection API"""
    print("=" * 50)
    print("POSE DETECTION TEST")
    print("=" * 50)
    
    # Create test image
    print("Creating test image...")
    img = create_test_image()
    print(f"Test image shape: {img.shape}")
    
    # Convert to base64
    _, buffer = cv2.imencode('.jpg', img)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    print(f"Image converted to base64: {len(img_base64)} characters")
    
    # Test REST API
    print("\nTesting REST API...")
    try:
        response = requests.post(
            'http://localhost:5000/api/detect-pose',
            json={'image': img_base64},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: REST API test successful!")
            print(f"Detected pose: {result.get('pose', 'unknown')}")
            print(f"Confidence: {result.get('confidence', 0):.2f}")
            print(f"Keypoints detected: {len(result.get('keypoints', []))}")
        else:
            print(f"FAILED: REST API test failed: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"FAILED: REST API test failed: {e}")
    
    # Test health endpoint
    print("\nTesting health endpoint...")
    try:
        response = requests.get('http://localhost:5000/health', timeout=5)
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: Health check successful!")
            print(f"Status: {result.get('status')}")
            print(f"Models loaded: {result.get('models_loaded')}")
            print(f"Classes: {result.get('classes')}")
        else:
            print(f"FAILED: Health check failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"FAILED: Health check failed: {e}")

if __name__ == "__main__":
    test_pose_detection()