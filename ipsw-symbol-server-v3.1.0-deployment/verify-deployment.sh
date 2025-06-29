#!/bin/bash
# IPSW Symbol Server v3.1.0 - Deployment Verification

echo "🔍 IPSW Symbol Server v3.1.0 - Deployment Verification"
echo "====================================================="

# Check package contents
echo "📦 Checking package contents..."
echo "Core Files:"
ls -la *.py *.yml *.sh | head -5
echo ""
echo "CLI Tools:"
ls -la cli-tools/
echo ""
echo "Docker Images:"
ls -lah docker-images/
echo ""
echo "Documentation:"
ls -la docs/

echo ""
echo "🐳 Docker Image Information:"
if [ -f "docker-images/ipsw-symbol-server-v3.1.0.tar.gz" ]; then
    echo "  ✅ Main application image: $(ls -lah docker-images/ipsw-symbol-server-v3.1.0.tar.gz | awk '{print $5}')"
fi

if [ -f "docker-images/postgres-13.tar.gz" ]; then
    echo "  ✅ PostgreSQL image: $(ls -lah docker-images/postgres-13.tar.gz | awk '{print $5}')"
fi

if [ -f "docker-images/nginx-alpine.tar.gz" ]; then
    echo "  ✅ Nginx image: $(ls -lah docker-images/nginx-alpine.tar.gz | awk '{print $5}')"
fi

echo ""
echo "🛠️ CLI Tools Verification:"
if [ -x "cli-tools/ipsw-dev-cli" ]; then
    echo "  ✅ ipsw-dev-cli: Available"
fi

if [ -x "cli-tools/symbolicate_v3.1.py" ]; then
    echo "  ✅ symbolicate_v3.1.py: Available"
fi

if [ -x "cli-tools/add_ipsw_v3.1.py" ]; then
    echo "  ✅ add_ipsw_v3.1.py: Available"
fi

echo ""
echo "🚀 Ready for deployment!"
echo "   Run: ./deploy.sh"
