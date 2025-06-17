#!/bin/bash
# Quick management commands

case "$1" in
    start)
        docker-compose up -d
        echo "✅ System started"
        ;;
    stop)
        docker-compose down
        echo "✅ System stopped"
        ;;
    restart)
        docker-compose restart
        echo "✅ System restarted"
        ;;
    logs)
        docker-compose logs -f
        ;;
    status)
        ./quick-deploy.sh
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|logs|status}"
        echo ""
        echo "start   - Start all services"
        echo "stop    - Stop all services"  
        echo "restart - Restart all services"
        echo "logs    - Show logs (follow)"
        echo "status  - Show system status"
        ;;
esac
