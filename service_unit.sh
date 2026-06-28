sudo tee /etc/systemd/system/env-ingest.service >/dev/null <<'EOF'
[Unit]
Description=Environmental monitoring MQTT to InfluxDB ingest
After=network-online.target mosquitto.service influxdb.service
Wants=network-online.target

[Service]
Type=simple
User=User
WorkingDirectory=/home/User/environmental-monitoring/ingest
ExecStart=/home/User/environmental-monitoring/ingest/.venv/bin/python /home/User/environmental-monitoring/ingest/ingest.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF