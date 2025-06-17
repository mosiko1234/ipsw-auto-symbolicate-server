#!/bin/bash
# תסריט לעדכון הגדרות S3 עבור רשת פנימית
# Script to update S3 configuration for internal network

echo "🔧 עדכון הגדרות S3 עבור רשת פנימית"
echo "=================================="

# Get current values
current_endpoint=$(grep "^S3_ENDPOINT=" env.symbol-server.txt | cut -d'=' -f2-)
current_bucket=$(grep "^S3_BUCKET=" env.symbol-server.txt | cut -d'=' -f2-)

echo "הגדרות נוכחיות:"
echo "S3_ENDPOINT: $current_endpoint"
echo "S3_BUCKET: $current_bucket"
echo ""

# Prompt for new values
read -p "כתובת S3 חדשה (לדוגמה: https://s3.company.local): " new_endpoint
read -p "שם Bucket (לדוגמה: ipsw-files): " new_bucket
read -p "האם להשתמש ב-SSL? (y/n) [y]: " use_ssl
read -p "האם לאמת תעודות SSL? (y/n) [n]: " verify_ssl

# Set defaults
use_ssl=${use_ssl:-y}
verify_ssl=${verify_ssl:-n}

# Convert to boolean
if [[ "$use_ssl" =~ ^[Yy]$ ]]; then
    ssl_value="true"
else
    ssl_value="false"
fi

if [[ "$verify_ssl" =~ ^[Yy]$ ]]; then
    verify_value="true"
else
    verify_value="false"
fi

# Update the file
if [[ ! -z "$new_endpoint" ]]; then
    echo "עדכון S3_ENDPOINT..."
    sed -i.bak "s|^S3_ENDPOINT=.*|S3_ENDPOINT=$new_endpoint|" env.symbol-server.txt
fi

if [[ ! -z "$new_bucket" ]]; then
    echo "עדכון S3_BUCKET..."
    sed -i.bak "s|^S3_BUCKET=.*|S3_BUCKET=$new_bucket|" env.symbol-server.txt
fi

echo "עדכון SSL settings..."
sed -i.bak "s|^S3_USE_SSL=.*|S3_USE_SSL=$ssl_value|" env.symbol-server.txt
sed -i.bak "s|^S3_VERIFY_SSL=.*|S3_VERIFY_SSL=$verify_value|" env.symbol-server.txt

# Copy to .env if exists
if [ -f ".env" ]; then
    echo "עדכון .env..."
    cp env.symbol-server.txt .env
fi

echo ""
echo "✅ ההגדרות עודכנו בהצלחה!"
echo ""
echo "הגדרות חדשות:"
echo "S3_ENDPOINT: $(grep "^S3_ENDPOINT=" env.symbol-server.txt | cut -d'=' -f2-)"
echo "S3_BUCKET: $(grep "^S3_BUCKET=" env.symbol-server.txt | cut -d'=' -f2-)"
echo "S3_USE_SSL: $(grep "^S3_USE_SSL=" env.symbol-server.txt | cut -d'=' -f2-)"
echo "S3_VERIFY_SSL: $(grep "^S3_VERIFY_SSL=" env.symbol-server.txt | cut -d'=' -f2-)"
echo ""
echo "להפעלת המערכת עם ההגדרות החדשות:"
echo "docker-compose -f docker-compose.symbol-server.yml up -d" 