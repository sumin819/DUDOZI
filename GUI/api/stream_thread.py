# stream_thread.py
import requests
import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal

class MJPEGStreamThread(QThread):
    frame_received = Signal(np.ndarray)
    error = Signal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self._running = True

    def run(self):
        try:
            r = requests.get(self.url, stream=True, timeout=None)
            bytes_buf = b""

            for chunk in r.iter_content(chunk_size=1024):
                if not self._running:
                    break

                bytes_buf += chunk
                a = bytes_buf.find(b'\xff\xd8')
                b = bytes_buf.find(b'\xff\xd9')

                if a != -1 and b != -1:
                    jpg = bytes_buf[a:b+2]
                    bytes_buf = bytes_buf[b+2:]

                    img = cv2.imdecode(
                        np.frombuffer(jpg, np.uint8),
                        cv2.IMREAD_COLOR
                    )
                    if img is not None:
                        self.frame_received.emit(img)

        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        self._running = False
        self.quit()
        self.wait()
