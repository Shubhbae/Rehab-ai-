#!/usr/bin/env python3
"""
Test script to verify LSTM model loading and functionality
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.lstm_service import LSTMClassifier
from app.services.movenet_service import MoveNetService
import numpy as np

def test_lstm_loading():
    """Test LSTM model loading"""
    print("🧪 Testing LSTM Model Loading...")
    try:
        lstm = LSTMClassifier()
        print(f"✅ LSTM initialized successfully")
        print(f"   - Model loaded: {lstm.model is not None}")
        print(f"   - Expected features: {lstm.expected_features}")
        return True
    except Exception as e:
        print(f"❌ LSTM loading failed: {e}")
        return False

def test_movenet_loading():
    """Test MoveNet model loading"""
    print("\n🧪 Testing MoveNet Model Loading...")
    try:
        movenet = MoveNetService()
        print("✅ MoveNet initialized successfully")
        return True
    except Exception as e:
        print(f"❌ MoveNet loading failed: {e}")
        return False

def test_prediction():
    """Test prediction with mock data"""
    print("\n🧪 Testing Prediction...")
    try:
        lstm = LSTMClassifier()
        
        # Create mock pose data (17 keypoints with x, y, score)
        mock_poses = []
        for frame in range(5):  # 5 frames
            frame_poses = []
            for i in range(17):  # 17 keypoints
                frame_poses.append({
                    "x": np.random.random(),
                    "y": np.random.random(), 
                    "score": np.random.random()
                })
            mock_poses.append(frame_poses)
        
        # Test prediction
        label, confidence, probs = lstm.predict_sequence(mock_poses)
        print(f"✅ Prediction successful:")
        print(f"   - Label: {label}")
        print(f"   - Confidence: {confidence:.3f}")
        print(f"   - Probabilities: {[f'{p:.3f}' for p in probs]}")
        return True
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Model Loading Tests...\n")
    
    results = []
    results.append(test_lstm_loading())
    results.append(test_movenet_loading())
    results.append(test_prediction())
    
    print(f"\n📊 Test Results:")
    print(f"   - Passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 All tests passed! Models are working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main())






