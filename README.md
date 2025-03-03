# paperless-sane-consumer

`paperless-sane-consumer` is a Docker image that automates the process of scanning documents using a scanner, uploading the scanned files to Paperless NGX, and exposing Prometheus metrics for monitoring.

## Features

- Scans documents using a connected scanner.
- Uploads scanned files to Paperless NGX.
- Exposes Prometheus metrics for monitoring scan success and failures

## Requirements

- Docker
- A compatible scanner with `sane` support.
- Paperless NGX instance with API access.

## Configuration

Set the following environment variables to configure the script:

- `PAPERLESS_API_URL`: URL of the Paperless NGX API.
- `PAPERLESS_API_TOKEN`: API token for Paperless NGX.
- `DEVICE`: Scanner device name (optional, will auto-detect if not set).
- `SCAN_MODE`: Scan mode (default: `color`).
- `SCAN_FORMAT`: Scan format (default: `pdf`).
- `SCAN_SOURCE`: Scan source (default: `Adf-duplex`).
- `SCAN_RESOLUTION`: Scan resolution (default: `300`).
- `SCAN_BLANK_PAGE_SKIP`: Skip blank pages (default: `yes`).
- `LOGLEVEL`: Logging level (default: `INFO`).

## Usage

### Docker Compose

You can use Docker Compose to run the container. Create a `docker-compose.yaml` file with the following content:

```yaml
version: '3.8'

services:
 paperless-sane-consumer:
    image: pascaaal/paperless-sane-consume:v1.1.1
    container_name: paperless-sane-consumer
    environment:
      - PAPERLESS_API_URL=https://your-paperless-instance.dev/api/documents/post_document/
      - PAPERLESS_API_TOKEN=YOUR_API_TOKEN
      - DEVICE=net:172.17.0.1:pfufs:fi-7160:003:003
      - SANE_IP=10.0.20.1
      # - DEBUG=true
    ports: # Exposing prometheus metrics
      - 8001:8000
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "-q","--spider", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Run the Docker Compose setup:
```sh
docker-compose up -d
```

## Prometheus Metrics

The following metrics are exposed:

- `scan_success_total`: Total number of successful scans.
- `scan_fail_total`: Total number of failed scans.
- `last_scan_timestamp`: Timestamp of the last successful scan.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.