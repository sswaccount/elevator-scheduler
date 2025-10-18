import subprocess
import sys

if __name__ == "__main__":
    cmd = [sys.executable, "-m", "app.scheduler", "direction_aware"]
    subprocess.run(cmd, check=True)
