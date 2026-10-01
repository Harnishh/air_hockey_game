# Webcam Air Hockey — Hand Tracking

The game now uses a webcam and MediaPipe hand landmarks to control the player's paddle. The mouse and keyboard remain available if the camera cannot start or no hand is visible.

## Requirements

- Python 3.10, 3.11, or 3.12 (MediaPipe publishes wheels for these versions)
- A webcam
- Internet access the first time the game starts, so it can download the official MediaPipe hand model

## Install and run

From this folder, create and activate a virtual environment, then install the dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

On macOS or Linux, activate the environment with `source .venv/bin/activate`.

The first launch downloads the model into `assets/hand_landmarker.task`. Later launches reuse that local file and do not need to download it again.

## Controls

- Hold your hand in view of the webcam and move your palm to control the paddle.
- Use WASD or the arrow keys to move the paddle manually.
- If the camera is unavailable or no hand is detected, the mouse also controls the paddle.
- Press Space to pause or resume.
- Press R to reset the puck.
- Press Escape to quit.

## How the hand control works

1. OpenCV captures a 640 by 480 webcam frame and mirrors it, like a selfie preview.
2. The frame is converted from OpenCV's BGR color format to RGB for MediaPipe.
3. MediaPipe Hand Landmarker finds 21 hand landmarks. This project averages landmarks 0, 5, 9, 13, and 17 to estimate a palm center. Those points are the wrist and the bases of the fingers, so the control point is steadier than a fingertip.
4. MediaPipe returns normalized coordinates from 0 to 1. The game scales X across the table width and Y across the player's half, then clamps the paddle to the lower rink area.
5. The paddle moves toward the mapped position gradually. This exponential smoothing reduces small tracking jitters.
6. If the hand disappears briefly, the paddle holds its last position for 0.8 seconds. Mouse and keyboard control remain available afterward.

The code uses MediaPipe's current Hand Landmarker Tasks API. The `.task` model is downloaded from Google's official model storage on first launch.