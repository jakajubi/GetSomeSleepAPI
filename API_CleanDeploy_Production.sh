#!/bin/bash

# Initialize
echo "   "
echo "--------------------------------------------------"
echo "--- Initializing ---------------------------------"
echo "--------------------------------------------------"
#source .venv/bin/activate
#sudo systemctl restart docker
#sudo usermod -aG docker $USER
#newgrp docker
docker ps

# Clean-up
echo "   "
echo "--------------------------------------------------"
echo "--- Remove all docker volumes --------------------"
echo "--------------------------------------------------"
docker compose down --rmi all --volumes --remove-orphans
docker system prune -af

# Remove specific volumes (if wanted)
echo "   "
echo "--------------------------------------------------"
echo "--- Removing specific volumes --------------------"
echo "--------------------------------------------------"
docker volume rm 20260216_getsomesleepapi_postgis_data_prod 2>/dev/null
docker volume rm 20260216_getsomesleepapi_minio_data_prod 2>/dev/null

# Rebuild and start (adjust IP adres)
echo "   "
echo "--------------------------------------------------"
echo "--- Rebuilding -----------------------------------"
echo "--------------------------------------------------"
docker compose -f docker-compose.prod.yml up -d --build

# Test API
echo "   "
echo "--------------------------------------------------"
echo "--- Test the API ---------------------------------"
echo "--------------------------------------------------"
sleep 5
curl http://192.168.1.49:5000/GetAPIStatus
