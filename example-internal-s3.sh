#!/bin/bash
# דוגמה לפריסה ברשת פנימית עם S3 פנימי
# Example deployment for internal network with internal S3

# הגדרת משתני הסביבה לS3 פנימי
# Set environment variables for internal S3
export S3_ENDPOINT="https://s3.internal.company.com"
export S3_BUCKET="ipsw-files"
export S3_USE_SSL="true"
export S3_VERIFY_SSL="false"  # For self-signed certificates

# הפעלת המערכת
# Deploy the system
./deploy-symbol-server.sh

# או הפעלה ידנית עם Docker Compose
# Or manual deployment with Docker Compose
# docker-compose -f docker-compose.symbol-server.yml up -d

echo "🎉 המערכת מוכנה עם S3 פנימי!"
echo "🌐 Web UI: http://localhost:5001"
echo "📡 API: http://localhost:8000"
echo "🗄️ S3: $S3_ENDPOINT/$S3_BUCKET" 