# Use Debian base image
FROM --platform=linux/amd64 debian:bookworm-slim

# Install required dependencies for Python, SANE, and pfufs package
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip sane sane-utils wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN rm /usr/lib/python*/EXTERNALLY-MANAGED && \
    pip3 install --no-cache-dir -r requirements.txt

# Download and install the pfufs package
RUN wget -O /tmp/pfufs.deb "https://origin.pfultd.com/downloads/IMAGE/fi/ubuntu/280/pfufs-ubuntu_2.8.0_amd64.deb" \
    && dpkg -i /tmp/pfufs.deb \
    && rm -f /tmp/pfufs.deb

# Set up entrypoint script to configure net.conf dynamically
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy the Python script
COPY paperless-sane-consumer.py /app/paperless-sane-consumer.py

# Create a non-root user and home directory
RUN useradd -m -s /bin/bash sane-consumer
# Set the permissions for the SANE configuration files
RUN chown -R sane-consumer:sane-consumer /etc/sane.d/

# Verify SANE installation
RUN scanimage -L || true

USER 1000

# Run the Python script
ENTRYPOINT ["/entrypoint.sh"]

