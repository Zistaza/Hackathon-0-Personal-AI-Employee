#!/bin/bash
# PM2 Auto-Start Setup Script
# Run this script with: bash enable_pm2_startup.sh

echo "=========================================="
echo "PM2 Auto-Start Configuration"
echo "=========================================="
echo ""
echo "This will configure PM2 to auto-start on system boot."
echo "You will be prompted for your sudo password."
echo ""

# Enable PM2 startup (properly quoted for paths with spaces)
sudo env "PATH=$PATH:/home/emizee/.nvm/versions/node/v24.13.1/bin" /home/emizee/.nvm/versions/node/v24.13.1/lib/node_modules/pm2/bin/pm2 startup systemd -u emizee --hp /home/emizee

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "PM2 will now automatically start your processes on system reboot."
echo ""
echo "Current PM2 processes:"
pm2 list
