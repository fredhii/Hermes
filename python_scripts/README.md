# Chat Application Implementation

Technical documentation for the chat message ingestion and processing system implementation using MQTT and PostgreSQL/AlloyDB.

## Features

### 🚀 Core Features
- **Real-time messaging** between multiple users
- **Message status tracking** (sent → received → read)
- **Typing indicators** to show when users are typing
- **Message history** stored in PostgreSQL
- **Broadcast messages** to all users
- **Interactive command-line interface**

### 📊 Message Status Flow
The application tracks message status similar to WhatsApp:

1. **📤 Sent** - Message sent from sender
2. **✅ Received by Server** - Message received by MQTT broker
3. **📥 Delivered** - Message delivered to recipient's device
4. **👁️ Read** - Message read by recipient

### 🗄️ Database Schema

#### `chat_messages` Table
```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id VARCHAR(255) UNIQUE NOT NULL,
    sender_id VARCHAR(100) NOT NULL,
    sender_name VARCHAR(100) NOT NULL,
    receiver_id VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'text',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### `message_status` Table
```sql
CREATE TABLE message_status (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id VARCHAR(100) NOT NULL,
    FOREIGN KEY (message_id) REFERENCES chat_messages(message_id) ON DELETE CASCADE
);
```

## Implementation Details

### Prerequisites
- Python 3.7+
- MQTT Broker (Mosquitto)
- PostgreSQL/AlloyDB Database

### Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
- `paho-mqtt` - MQTT client library
- `psycopg2-binary` - PostgreSQL adapter

### Architecture Components
- **MQTT Client**: Handles real-time message publishing and subscription
- **Database Layer**: PostgreSQL/AlloyDB for persistent message storage
- **Status Tracking**: Real-time message delivery status monitoring
- **Interactive Interface**: Command-line chat interface with status updates

## Configuration

### Environment Variables
Set these environment variables or use the defaults:

```bash
# MQTT Configuration
MQTT_BROKER_HOST=localhost
MQTT_TOPIC=chat/messages

# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_DB=public
POSTGRES_USER=dbowner
POSTGRES_PASSWORD=uX3_YnF3y485NziMN6xW

# Chat User Configuration
CHAT_USER_ID=fredy
CHAT_USER_NAME=Fredy
```

## Usage

### Quick Start with Docker Compose (Recommended)
1. **Start all services:**
   ```bash
   ./run_chat.sh start
   ```

2. **Connect to chat clients:**
   ```bash
   # Connect to Fredy's chat (Publisher)
   ./run_chat.sh attach-publisher
   
   # Connect to David's chat (Subscriber) - in another terminal
   ./run_chat.sh attach-subscriber
   ```

3. **View logs:**
   ```bash
   ./run_chat.sh logs
   ```

### Manual Start (Local Python)
1. **Start the demo script:**
   ```bash
   python run_chat_demo.py
   ```

2. **Or run individual clients:**
   ```bash
   # Terminal 1 - Fredy (Publisher)
   python publisher.py
   
   # Terminal 2 - David (Subscriber)
   python subscriber.py
   
   # Or with custom user names:
   # CHAT_USER_ID=alice CHAT_USER_NAME="Alice" python publisher.py
   # CHAT_USER_ID=bob CHAT_USER_NAME="Bob" python subscriber.py
   
   # Or with Docker Compose (using the same database as AlloyDB)
   # Make sure docker-compose.yml services are running first
   ```bash
   # Start all services (MQTT, Database, and Chat)
   docker-compose up -d
   
   # Or use the management script
   ./run_chat.sh start
   ```
   ```

### Chat Commands

Once in the chat interface, you can use these commands:

| Command | Description | Example |
|---------|-------------|---------|
| `send <user_id> <message>` | Send message to specific user | `send user2 Hello there!` |
| `broadcast <message>` | Send message to all users | `broadcast Hello everyone!` |
| `history [limit]` | Show message history | `history 10` |
| `status` | Show pending message status | `status` |
| `typing <user_id>` | Send typing indicator | `typing user2` |
| `help` | Show help | `help` |
| `quit` | Exit chat | `quit` |

### Example Chat Session

```
🎉 Welcome to the chat, Fredy!
Your ID: fredy

==================================================
💬 CHAT COMMANDS
==================================================
send <user_id> <message>  - Send message to user
broadcast <message>       - Send message to all users
history [limit]           - Show message history
status                    - Show pending message status
typing <user_id>          - Send typing indicator
help                      - Show this help
quit                      - Exit chat
==================================================

[Fredy] send david Hello! How are you?

📤 Message sent: Hello! How are you?

[Fredy] typing david

✍️ Fredy is typing...

💬 [14:30:25] David: Hi! I'm doing great, thanks!

👁️ Sent read receipt for message a1b2c3d4...

✅ Message a1b2c3d4... received_by_server by david
👁️ Message a1b2c3d4... read by david
```

## Architecture

### MQTT Topics
- `chat/messages` - General chat topic for all messages
- `chat/messages/{user_id}` - User-specific topic for direct messages and status updates

### Message Types
1. **Message** (`type: "message"`) - Regular chat messages
2. **Status** (`type: "status"`) - Message status updates
3. **Typing** (`type: "typing"`) - Typing indicators

### Message Flow
```
User A sends message → MQTT Broker → User B receives message
User B reads message → Send read receipt → User A receives status update
```

## Development

### Project Structure
```
Hermes/
├── docker-compose.yml    # Main services configuration
├── run_chat.sh          # Chat service management script
├── python_scripts/
│   ├── publisher.py      # Chat publisher/client
│   ├── subscriber.py     # Chat subscriber/client
│   ├── Dockerfile        # Docker configuration
│   ├── requirements.txt  # Python dependencies
│   └── README_CHAT.md    # This file
└── mosquitto.conf        # MQTT broker configuration
```

### Adding New Features
1. **New Message Types**: Add new message type handling in `on_message()`
2. **Database Schema**: Modify `setup_database()` method
3. **Status Types**: Add new status types to status tracking system

### Testing
To test the application:
1. Start MQTT broker and PostgreSQL
2. Run multiple chat clients with different user IDs
3. Send messages between users
4. Verify status tracking works correctly

## Troubleshooting

### Common Issues

**Connection Failed**
- Ensure MQTT broker is running
- Check MQTT_BROKER_HOST configuration
- Verify network connectivity

**Database Connection Failed**
- Ensure PostgreSQL is running
- Check database credentials
- Verify database exists

**Messages Not Received**
- Check user IDs match between sender and receiver
- Verify MQTT topic subscriptions
- Check message format

### Debug Mode
Add debug logging by modifying the MQTT client configuration:
```python
client.enable_logger()
```

## License

This project is open source and available under the MIT License.
