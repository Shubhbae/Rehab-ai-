#!/usr/bin/env python3
"""
Simple pose detection test
"""
import requests
import base64
import numpy as np
import cv2

def create_simple_test_image():
    """Create a very simple test image"""
    # Create a small 100x100 test image
    img = np.ones((100, 100, 3), dtype=np.uint8) * 128  # Gray image
    return img

def test_simple_pose():
    """Test pose detection with a simple image"""
    print("Testing simple pose detection...")
    
    # Create simple test image
    img = create_simple_test_image()
    print(f"Test image shape: {img.shape}")
    
    # Convert to base64
    _, buffer = cv2.imencode('.jpg', img)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    print(f"Image base64 length: {len(img_base64)}")
    
    # Test with shorter timeout
    try:
        response = requests.post(
            'http://localhost:5000/api/detect-pose',
            json={'image': img_base64},
            timeout=30  # Longer timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: Pose detection worked!")
            print(f"Result: {result}")
        else:
            print(f"FAILED: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_simple_pose()
