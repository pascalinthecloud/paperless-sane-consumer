#!/bin/bash
set -e

# Ensure the SANE_IP is set, defaulting if not provided
SANE_IP="${SANE_IP:-172.17.0.1}"

# Configure SANE net.conf dynamically
echo -e "connect_timeout = 60\n$SANE_IP" > /etc/sane.d/net.conf

# Run the main command
exec python3 -u /app/paperless-sane-consumer.py
