#!/bin/bash

echo "Stopping the Flask application using systemd..."
sudo systemctl stop howkiki  # systemd 서비스 중지
echo "Flask application stopped."
