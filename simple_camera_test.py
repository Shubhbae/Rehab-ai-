#!/usr/bin/env python3
"""
Simple camera test to verify 17 joint points tracking
"""
import cv2
import numpy as np
from app.services.lstm_service import LSTMClassifier
from app.services.movenet_service import MoveNetService

def main():
    print("Starting Simple Camera Test...")
    
    # Load services
    print("Loading H5 model...")
    lstm = LSTMClassifier()
    print("Loading MoveNet...")
    movenet = MoveNetService()
    
    # Try different camera indices
    camera_indices = [0, 1, 2]
    cap = None
    
    for idx in camera_indices:
        print(f"Trying camera index {idx}...")
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"Camera {idx} working! Frame shape: {frame.shape}")
                break
            else:
                cap.release()
                cap = None
        else:
            cap.release()
            cap = None
    
    if cap is None:
        print("No working camera found!")
        return
    
    print("Press 'q' to quit, 's' to save frame")
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame")
            break
        
        frame_count += 1
        
        # Run MoveNet detection every 5 frames to reduce load
        if frame_count % 5 == 0:
            try:
                poses = movenet.detect_keypoints(frame)
                print(f"Frame {frame_count}: Detected {len(poses)} keypoints")
                
                if len(poses) == 17:
                    # Run LSTM prediction
                    label, conf, probs = lstm.predict_sequence([poses])
                    print(f"  -> Prediction: {label} (confidence: {conf:.3f})")
                    
                    # Draw skeleton on frame
                    draw_skeleton(frame, poses)
                else:
                    print(f"  -> Not enough keypoints: {len(poses)}/17")
                    
            except Exception as e:
                print(f"Error in detection: {e}")
        
        # Display frame
        cv2.imshow('Pose Detection Test', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            cv2.imwrite(f'frame_{frame_count}.jpg', frame)
            print(f"Saved frame_{frame_count}.jpg")
    
    cap.release()
    cv2.destroyAllWindows()
    print("Test completed!")

def draw_skeleton(frame, poses):
    """Draw skeleton on frame"""
    if len(poses) != 17:
        return
    
    # MoveNet skeleton connections
    connections = [
        [0, 1], [0, 2], [1, 3], [2, 4],    # Head
        [5, 6],                             # Shoulders
        [5, 7], [7, 9],                     # Left arm
        [6, 8], [8, 10],                    # Right arm
        [5, 11], [6, 12], [11, 12],        # Torso
        [11, 13], [13, 15],                 # Left leg
        [12, 14], [14, 16]                  # Right leg
    ]
    
    h, w = frame.shape[:2]
    
    # Draw connections
    for connection in connections:
        pt1_idx, pt2_idx = connection
        if pt1_idx < len(poses) and pt2_idx < len(poses):
            pt1 = poses[pt1_idx]
            pt2 = poses[pt2_idx]
            
            if pt1['score'] > 0.3 and pt2['score'] > 0.3:
                x1, y1 = int(pt1['x'] * w), int(pt1['y'] * h)
                x2, y2 = int(pt2['x'] * w), int(pt2['y'] * h)
                cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    
    # Draw keypoints
    for i, pose in enumerate(poses):
        if pose['score'] > 0.3:
            x, y = int(pose['x'] * w), int(pose['y'] * h)
            cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)
            cv2.circle(frame, (x, y), 6, (255, 255, 255), 1)

if __name__ == "__main__":
    main()


