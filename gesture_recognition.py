import cv2
import mediapipe as mp
import urllib.request
import os

class GestureRecognizer:
    def __init__(self, video_writer_path=None):
        self.video_writer_path = video_writer_path
        self.video_writer = None
        self.model_path = "hand_landmarker.task"
        if not os.path.exists(self.model_path):
            print("[Camera] Downloading Hand Landmarker AI model. This only happens once...")
            url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
            try:
                urllib.request.urlretrieve(url, self.model_path)
                print("[Camera] Model downloaded successfully.")
            except Exception as e:
                print(f"[Camera] Failed to download model: {e}")

        base_options = mp.tasks.BaseOptions(model_asset_path=self.model_path)
        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=1,
            min_hand_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.detector = mp.tasks.vision.HandLandmarker.create_from_options(options)
        self.cap = cv2.VideoCapture(0)

        # Setup Video Writer
        if self.video_writer_path:
            frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            if fps == 0 or fps > 60:
                fps = 20.0
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(self.video_writer_path, fourcc, fps, (frame_width, frame_height))

    def is_open_palm(self, hand_landmarks):
        tips = [8, 12, 16, 20]
        pips = [6, 10, 14, 18]
        open_fingers = 0
        for tip, pip in zip(tips, pips):
            if hand_landmarks[tip].y < hand_landmarks[pip].y:
                open_fingers += 1
        return open_fingers == 4

    def run(self):
        print("[Camera] Starting camera... Show an Open Palm (all 4 main fingers up) to stop.")
        while True:
            success, img = self.cap.read()
            if not success:
                continue

            # Save clean frame to video
            if self.video_writer:
                self.video_writer.write(img)

            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
            
            results = self.detector.detect(mp_image)

            if results.hand_landmarks:
                for hand_landmarks in results.hand_landmarks:
                    h, w, _ = img.shape
                    for lm in hand_landmarks:
                        x, y = int(lm.x * w), int(lm.y * h)
                        cv2.circle(img, (x, y), 5, (0, 255, 0), -1)
                    
                    if self.is_open_palm(hand_landmarks):
                        print("[Camera] Open Palm gesture detected! Stopping application...")
                        cv2.putText(img, "STOP GESTURE DETECTED!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                        cv2.imshow("Gesture Control (Esc to force quit)", img)
                        cv2.waitKey(1000)
                        self.cap.release()
                        if self.video_writer:
                            self.video_writer.release()
                        cv2.destroyAllWindows()
                        return True

            cv2.imshow("Gesture Control (Esc to force quit)", img)
            if cv2.waitKey(1) & 0xFF == 27:
                print("[Camera] Escape key pressed. Exiting...")
                break
                
        self.cap.release()
        if self.video_writer:
            self.video_writer.release()
        cv2.destroyAllWindows()
        return False
