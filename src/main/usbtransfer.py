import subprocess
import threading
import traceback
import re

class USBTransfer:
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst

        self.progress = 0
        self.speed = "0MB/s"
        self.transferred = "0GB"
        self.total = f"{(float(src['size']) - float(src['free'])):.2f}GB"
        
        self.running = False
        self.finished = False
        self.error = False

        self._process = None

    def start(self):
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

    def _run(self):
        self.running = True
        self.finished = False
        self.error = False

        try:
            self._process = subprocess.Popen(
                [
                    "rsync",
                    "-av",
                    "--info=progress2",
                    "--partial",
                    self.src["mount"],
                    self.dst["mount"]
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            for line in self._process.stdout:
                self._parse_progress(line.strip())
            self._process.wait()

            if self._process.returncode == 0:
                self.finished = True
            else:
                self.error = True
        except Exception as error:
            self.error = True
            print(error)
        self.running = False

    def _parse_progress(self, line):
        # example:
        # 123,456,789  42%   5.00MB/s    0:00:10

        match = re.search(
            r'([\d,]+)\s+(\d+)%\s+([\d\.]+[A-Za-z/]+)',
            line
        )

        if match:
            # --- data transferred (in gb) ---
            bytes_val = int(match.group(1).replace(",", ""))
            self.transferred = f"{bytes_val / (1024**3):.2f}GB"

            # --- progress ---
            self.progress = int(match.group(2))

            # --- speed ---
            self.speed = match.group(3)

    def stop(self):
        if self._process and self.running:
            self._process.terminate()
            self.running = False
            self.error = True
