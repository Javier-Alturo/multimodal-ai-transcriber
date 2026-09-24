import threading
import time

import cv2


class VideoRecorder:
    """Graba video de la camara sin procesamiento de vision por computador."""

    def __init__(self, video_path, camera_index=0, show_preview=True):
        self.video_path = video_path
        self.camera_index = camera_index
        self.show_preview = show_preview
        self.stop_event = threading.Event()
        self.thread = None
        self.frame_count = 0
        self.start_time = None
        self.end_time = None

    def start(self):
        self.frame_count = 0
        self.start_time = None
        self.end_time = None
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._record_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=5)
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            if duration > 0:
                return self.frame_count / duration
        return 20.0

    def _record_loop(self):
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            print("[Video] No se pudo abrir la camara.")
            return

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(self.video_path, fourcc, 20.0, (width, height))

        self.start_time = time.time()
        window_name = "Grabando (Enter en consola para detener)"

        while not self.stop_event.is_set():
            success, frame = cap.read()
            if not success:
                continue

            writer.write(frame)
            self.frame_count += 1

            if self.show_preview:
                cv2.imshow(window_name, frame)
                if cv2.waitKey(1) & 0xFF == 27:
                    self.stop_event.set()
                    break

        self.end_time = time.time()
        cap.release()
        writer.release()
        if self.show_preview:
            cv2.destroyAllWindows()

        duration = self.end_time - self.start_time
        fps = self.frame_count / duration if duration > 0 else 0
        print(f"[Video] {self.frame_count} frames en {duration:.1f}s ({fps:.1f} fps real)")
