import os
import time
import subprocess
import requests
import logging
import threading
from prometheus_client import start_http_server, Counter, Gauge
from flask import Flask

# Paperless NGX API settings
PAPERLESS_API_URL = os.getenv("PAPERLESS_API_URL")
PAPERLESS_API_TOKEN = os.getenv("PAPERLESS_API_TOKEN")

# Prometheus metrics
SCAN_SUCCESS = Counter('scan_success_total',
                       'Total number of successful scans')
SCAN_FAIL = Counter('scan_fail_total', 'Total number of failed scans')
LAST_SCAN_TIMESTAMP = Gauge('last_scan_timestamp',
                            'Timestamp of the last successful scan')

# Scan settings
DEVICE = os.getenv("DEVICE")

SCAN_MODE = os.getenv("SCAN_MODE", "color")
SCAN_FORMAT = os.getenv("SCAN_FORMAT", "pdf")
SCAN_SOURCE = os.getenv("SCAN_SOURCE", "Adf-duplex")
SCAN_RESOLUTION = os.getenv("SCAN_RESOLUTION", "300")
SCAN_BLANK_PAGE_SKIP = os.getenv("SCAN_BLANK_PAGE_SKIP", "yes")

# Set up logging
LOGLEVEL = os.getenv("LOGLEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s - [%(levelname)s] - %(message)s"
logging.basicConfig(
    level=LOGLEVEL,
    format=LOG_FORMAT
)

logger = logging.getLogger()

app = Flask(__name__)

@app.route('/health')
def health():
    return "OK", 200


def validate_env_vars() -> bool:
    """Validate required environment variables and check for scanner device."""
    missing_vars = []
    if not PAPERLESS_API_URL:
        missing_vars.append("PAPERLESS_API_URL")
    if not PAPERLESS_API_TOKEN:
        missing_vars.append("PAPERLESS_API_TOKEN")
    if not DEVICE:
        missing_vars.append("DEVICE")
        find_scanner()

    if missing_vars:
        logger.error(
            f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    return True


def find_scanner() -> None:
    """Find and log the connected scanner device."""
    cmd = ["scanimage", "-L"]
    result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, text=True)
    logger.info(f"Found scanner: {result.stdout}")


def run_scan() -> None:
    """Run the scanning process and handle the results."""
    if not validate_env_vars():
        SCAN_FAIL.inc()
        return
    filename = time.strftime("%Y%m%d_%H%M%S") + ".pdf"
    cmd = [
        "scanimage", "--device=" + DEVICE,
        "--mode", SCAN_MODE, "--format=" + SCAN_FORMAT, "--source=" + SCAN_SOURCE,
        "--resolution=" + SCAN_RESOLUTION, "--batch=" + filename,
        "--blank-page-skip=" + SCAN_BLANK_PAGE_SKIP
    ]

    try:
        stdout_option = None if LOGLEVEL == "DEBUG" else subprocess.DEVNULL
        stderr_option = None if LOGLEVEL == "DEBUG" else subprocess.DEVNULL
        result = subprocess.run(
            cmd, check=True, stdout=stdout_option, stderr=stderr_option)
        exit_code = result.returncode

        logger.info(f"result.returncode: {exit_code}")

        if result.returncode == 0:
            logger.info("Scan successful, uploading files to Paperless...")
            upload_scanned_files(filename)
            SCAN_SUCCESS.inc()
            LAST_SCAN_TIMESTAMP.set(time.time())
        else:
            logger.error(f"Scan failed with exit code {exit_code}.")
            SCAN_FAIL.inc()

    except subprocess.CalledProcessError as e:
        if e.returncode == 7:
            logger.info("No paper detected, skipping scan.")
        else:
            logger.debug(f"Scan failed with error. {e}")
            logger.error("Scan failed.")
            SCAN_FAIL.inc()


def upload_scanned_files(file_path: str) -> None:
    """Upload scanned files to Paperless and handle the response."""
    logger.info(f"Uploading {file_path} to Paperless...")
    headers = {"Authorization": f"Token {PAPERLESS_API_TOKEN}"}
    try:
        with open(file_path, "rb") as file:
            files = {"document": file}
            response = requests.post(
                PAPERLESS_API_URL, headers=headers, files=files)

        if response.status_code == 200:
            logger.info(
                f"File {file_path} successfully uploaded to Paperless.")
            os.remove(file_path)
        else:
            logger.error(
                f"Error uploading {file_path}: {response.status_code}, {response.text}")
    except Exception as e:
        logger.error(f"Failed to upload {file_path}: {e}")


def run_flask():
    """Run the Flask app."""
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host="0.0.0.0", port=5000)

def main() -> None:
    """Main function to start the Prometheus server and run scans periodically."""
    start_http_server(8000)
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    while True:
        run_scan()
        time.sleep(15)


if __name__ == "__main__":
    main()
