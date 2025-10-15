import subprocess
import sys

if __name__ == "__main__":
    cmd = [sys.executable, "-m", "app.scheduler", "shortest"]
    subprocess.run(cmd, check=True)
