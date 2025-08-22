#!/bin/bash

# Chat Service Management Script

echo "🎉 Chat Service Manager"
echo "========================"

case "$1" in
    "start")
        echo "🚀 Starting all chat services..."
        docker-compose up -d mqtt-broker db
        echo "⏳ Waiting for database to be ready..."
        sleep 5
        docker-compose up -d chat-publisher chat-subscriber
        echo "✅ All services started!"
        echo ""
        echo "📋 Available commands:"
        echo "  ./run_chat.sh attach-publisher  - Connect to Fredy's chat"
        echo "  ./run_chat.sh attach-subscriber - Connect to David's chat"
        echo "  ./run_chat.sh logs              - View all logs"
        echo "  ./run_chat.sh stop              - Stop all services"
        ;;
    "attach-publisher")
        echo "🔗 Connecting to Fredy's chat (Publisher)..."
        docker attach chat-publisher
        ;;
    "attach-subscriber")
        echo "🔗 Connecting to David's chat (Subscriber)..."
        docker attach chat-subscriber
        ;;
    "logs")
        echo "📋 Showing logs for all chat services..."
        docker-compose logs -f chat-publisher chat-subscriber
        ;;
    "stop")
        echo "🛑 Stopping all chat services..."
        docker-compose stop chat-publisher chat-subscriber
        echo "✅ Chat services stopped!"
        echo "💡 To stop all services (including MQTT and DB), run: docker-compose down"
        ;;
    "restart")
        echo "🔄 Restarting chat services..."
        docker-compose restart chat-publisher chat-subscriber
        echo "✅ Chat services restarted!"
        ;;
    "status")
        echo "📊 Service Status:"
        docker-compose ps
        ;;
    *)
        echo "❌ Invalid command. Available commands:"
        echo ""
        echo "  start              - Start all chat services"
        echo "  attach-publisher   - Connect to Fredy's chat"
        echo "  attach-subscriber  - Connect to David's chat"
        echo "  logs               - View all logs"
        echo "  stop               - Stop chat services"
        echo "  restart            - Restart chat services"
        echo "  status             - Show service status"
        echo ""
        echo "💡 Example: ./run_chat.sh start"
        ;;
esac
