mkdir -p ~/environmental-monitoring/mosquitto/config
cd ~/environmental-monitoring

cat > mosquitto/config/mosquitto.conf <<'EOF'
listener 1883
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
EOF