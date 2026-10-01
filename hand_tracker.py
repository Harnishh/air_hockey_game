"""Webcam capture and palm landmark tracking with MediaPipe Tasks."""

from pathlib import Path
import shutil
import time
import urllib.request


MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/latest/hand_landmarker.task"
)
MODEL_PATH = Path(__file__).parent / "assets" / "hand_landmarker.task"
PALM_LANDMARK_IDS = (0, 5, 9, 13, 17)


class HandTracker:
    """Read webcam frames and return the normalized center of the palm."""

    def __init__(self, camera_index=0):
        import cv2
        import mediapipe as mp

        self.cv2 = cv2
        self.mp = mp
        self._ensure_model_file()

        self.camera = cv2.VideoCapture(camera_index)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        if not self.camera.isOpened():
            self.camera.release()
            raise RuntimeError(
                f"Could not open webcam {camera_index}. Check that it is connected "
                "and not being used by another app."
            )

        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(MODEL_PATH)),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        try:
            self.landmarker = mp.tasks.vision.HandLandmarker.create_from_options(
                options
            )
        except Exception:
            self.camera.release()
            raise

        self.last_timestamp_ms = 0

    @staticmethod
    def _ensure_model_file():
        """Download the small official model once and keep it in assets/."""
        if MODEL_PATH.exists():
            return

        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = MODEL_PATH.with_suffix(".download")
        print("Downloading the MediaPipe hand model (one-time setup)...")
        try:
            with urllib.request.urlopen(MODEL_URL, timeout=30) as response:
                with temporary_path.open("wb") as model_file:
                    shutil.copyfileobj(response, model_file)
            temporary_path.replace(MODEL_PATH)
        except Exception as error:
            temporary_path.unlink(missing_ok=True)
            raise RuntimeError(
                "Could not download the MediaPipe hand model. Check your internet "
                "connection, then start the game again. Model URL: " + MODEL_URL
            ) from error

    def read(self):
        """Return a mirrored RGB preview and palm (x, y), or None if not found."""
        success, frame = self.camera.read()
        if not success:
            return None, None

        # Mirror the camera so moving your hand left feels like moving left on screen.
        frame = self.cv2.flip(frame, 1)
        rgb_frame = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)
        mp_image = self.mp.Image(
            image_format=self.mp.ImageFormat.SRGB,
            data=rgb_frame,
        )

        # VIDEO mode expects strictly increasing timestamps for successive frames.
        timestamp_ms = int(time.monotonic() * 1000)
        timestamp_ms = max(timestamp_ms, self.last_timestamp_ms + 1)
        self.last_timestamp_ms = timestamp_ms
        result = self.landmarker.detect_for_video(mp_image, timestamp_ms)

        if not result.hand_landmarks:
            return rgb_frame, None

        landmarks = result.hand_landmarks[0]
        palm_x = sum(landmarks[index].x for index in PALM_LANDMARK_IDS) / len(
            PALM_LANDMARK_IDS
        )
        palm_y = sum(landmarks[index].y for index in PALM_LANDMARK_IDS) / len(
            PALM_LANDMARK_IDS
        )

        frame_height, frame_width = rgb_frame.shape[:2]
        for index in PALM_LANDMARK_IDS:
            landmark_x = int(landmarks[index].x * frame_width)
            landmark_y = int(landmarks[index].y * frame_height)
            self.cv2.circle(
                rgb_frame, (landmark_x, landmark_y), 4, (65, 235, 160), -1
            )

        center_x = int(palm_x * frame_width)
        center_y = int(palm_y * frame_height)
        self.cv2.circle(rgb_frame, (center_x, center_y), 9, (255, 190, 55), -1)
        return rgb_frame, (palm_x, palm_y)

    def close(self):
        """Release the webcam and shut down MediaPipe cleanly."""
        self.camera.release()
        self.landmarker.close()