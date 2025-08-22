# Hermes - Real-time Chat Message Ingestion and Processing System

A real-time data pipeline that implements and validates a prototype for a chat message ingestion and processing system using MQTT and PostgreSQL (AlloyDB).

## 🎯 Project Overview

Hermes is a comprehensive chat system that demonstrates real-time message processing with the following capabilities:

- **Real-time messaging** between multiple users via MQTT
- **Message status tracking** (sent → received → read) similar to WhatsApp
- **Persistent storage** in PostgreSQL/AlloyDB with full message history
- **Typing indicators** and interactive chat features
- **Containerized deployment** with Docker Compose

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Chat Client   │    │   Chat Client   │    │   Chat Client   │
│   (Fredy)       │    │   (David)       │    │   (Any User)    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │      MQTT Broker          │
                    │   (Mosquitto)             │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │   PostgreSQL/AlloyDB      │
                    │   (Message Storage)       │
                    └───────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### 1. Clone and Start
```bash
# Clone the repository
git clone <repository-url>
cd Hermes

# Start all services
./run_chat.sh start
```

### 2. Connect to Chat Clients
```bash
# Terminal 1 - Connect to Fredy's chat
./run_chat.sh attach-publisher

# Terminal 2 - Connect to David's chat (in new terminal)
./run_chat.sh attach-subscriber
```

### 3. Start Chatting
Once connected, use these commands:
- `send david Hello!` - Send message to David
- `broadcast Hello everyone!` - Send to all users
- `history 10` - Show last 10 messages
- `status` - Show message status
- `typing david` - Send typing indicator
- `help` - Show all commands
- `quit` - Exit chat

## 📊 Message Processing Pipeline

### Message Flow
1. **📤 Sent** - User sends message via chat client
2. **✅ Received by Server** - MQTT broker receives message
3. **📥 Delivered** - Message delivered to recipient's device
4. **👁️ Read** - Recipient reads message (with read receipt)

### Data Storage
- **`chat_messages`** table stores all messages with metadata
- **`message_status`** table tracks message delivery status with timestamps
- Full message history with sender, receiver, content, and timestamps

## 🛠️ Services

### Core Services
| Service | Description | Port |
|---------|-------------|------|
| `mqtt-broker` | Mosquitto MQTT broker for real-time messaging | 1883 |
| `db` | PostgreSQL/AlloyDB database for message storage | 5432 |
| `chat-publisher` | Fredy's chat client (Publisher) | - |
| `chat-subscriber` | David's chat client (Subscriber) | - |

### Management Commands
```bash
./run_chat.sh start              # Start all services
./run_chat.sh attach-publisher   # Connect to Fredy's chat
./run_chat.sh attach-subscriber  # Connect to David's chat
./run_chat.sh logs               # View service logs
./run_chat.sh status             # Check service status
./run_chat.sh stop               # Stop chat services
./run_chat.sh restart            # Restart chat services
```

## 🗄️ Database Schema

### Chat Messages Table
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

### Message Status Table
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

## 🔧 Configuration

### Environment Variables
```bash
# MQTT Configuration
MQTT_BROKER_HOST=mqtt-broker
MQTT_TOPIC=chat/messages

# Database Configuration
POSTGRES_HOST=db
POSTGRES_DB=public
POSTGRES_USER=dbowner
POSTGRES_PASSWORD=uX3_YnF3y485NziMN6xW

# Chat User Configuration
CHAT_USER_ID=fredy
CHAT_USER_NAME=Fredy
```

### MQTT Topics
- `chat/messages` - General chat topic for all messages
- `chat/messages/{user_id}` - User-specific topic for direct messages and status updates

## 📁 Project Structure
```
Hermes/
├── docker-compose.yml          # Main services configuration
├── run_chat.sh                # Chat service management script
├── mosquitto.conf             # MQTT broker configuration
├── README.md                  # This file
└── python_scripts/
    ├── publisher.py           # Chat publisher/client
    ├── subscriber.py          # Chat subscriber/client
    ├── Dockerfile             # Docker configuration
    ├── requirements.txt       # Python dependencies
    └── README_CHAT.md         # Detailed chat documentation
```

## 🧪 Testing and Validation

### Message Processing Validation
1. **Send a message** from Fredy to David
2. **Verify status flow**: sent → received_by_server → read
3. **Check database** for message persistence
4. **Test typing indicators** and real-time features

### Example Test Session
```bash
# Start services
./run_chat.sh start

# Connect to Fredy
./run_chat.sh attach-publisher
# In Fredy's chat: send david Test message

# Connect to David
./run_chat.sh attach-subscriber
# Verify message received and status updates
```

## 🔍 Monitoring and Logs

### View Service Logs
```bash
# All chat services
./run_chat.sh logs

# Specific service
docker-compose logs chat-publisher
docker-compose logs chat-subscriber
```

### Database Queries
```sql
-- View all messages
SELECT * FROM chat_messages ORDER BY created_at DESC;

-- View message status
SELECT * FROM message_status ORDER BY timestamp DESC;

-- Messages between specific users
SELECT * FROM chat_messages 
WHERE (sender_id = 'fredy' AND receiver_id = 'david') 
   OR (sender_id = 'david' AND receiver_id = 'fredy')
ORDER BY created_at DESC;
```

## 🚀 Deployment

### Production Considerations
- **Security**: Add authentication to MQTT broker
- **Scalability**: Use external PostgreSQL/AlloyDB instance
- **Monitoring**: Add health checks and metrics
- **Backup**: Implement database backup strategy

### Development
```bash
# Start development environment
docker-compose up -d

# View logs in real-time
docker-compose logs -f

# Access database
docker exec -it alloydb psql -U dbowner -d public
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Troubleshooting

### Common Issues

**Services won't start**
```bash
# Check if ports are available
docker-compose ps
# Restart services
./run_chat.sh restart
```

**Can't connect to chat**
```bash
# Check MQTT broker status
docker-compose logs mqtt-broker
# Verify database connection
docker-compose logs db
```

**Messages not persisting**
```bash
# Check database logs
docker-compose logs db
# Verify database schema
docker exec -it alloydb psql -U dbowner -d public -c "\dt"
```

For more detailed information, see [python_scripts/README_CHAT.md](python_scripts/README_CHAT.md).


### Bonus - DuckDB

```
root@ee5c00720fe2:/# duckdb
-- Loading resources from /root/.duckdbrc
v0.8.1 6536a77232
Enter ".help" for usage hints.
Connected to a transient in-memory database.
Use ".open FILENAME" to reopen on a persistent database.
duckdb > INSTALL postgres;
duckdb > 
duckdb > LOAD postgres;
duckdb > -- Scan the table "mytable" from the schema "public" in the database "mydb"
duckdb > SELECT * FROM postgres_scan('host=db port=5432 dbname=mydb user=dbowner password=uX3_YnF3y485NziMN6xW', 'public', 'chat_messages');
Error: IO Error: Unable to connect to Postgres at host=db port=5432 dbname=mydb user=dbowner password=uX3_YnF3y485NziMN6xW: connection to server at "db" (172.19.0.2), port 5432 failed: FATAL:  database "mydb" does not exist

duckdb > SELECT * FROM postgres_scan('host=db port=5432 dbname=public user=dbowner password=uX3_YnF3y485NziMN6xW', 'public', 'chat_messages');
┌──────────────────────┬──────────────────────┬───────────┬─────────────┬─────────────┬─────────┬──────────────┬──────────────────────┬──────────────────────┐
│          id          │      message_id      │ sender_id │ sender_name │ receiver_id │ content │ message_type │      created_at      │      updated_at      │
│         uuid         │       varchar        │  varchar  │   varchar   │   varchar   │ varchar │   varchar    │ timestamp with tim…  │ timestamp with tim…  │
├──────────────────────┼──────────────────────┼───────────┼─────────────┼─────────────┼─────────┼──────────────┼──────────────────────┼──────────────────────┤
│ 4780c7fe-642d-44d5…  │ 25ab79e2-ea7c-4c46…  │ user1     │ User 1      │ user2       │ hola    │ text         │ 2025-08-22 21:39:2…  │ 2025-08-22 21:39:2…  │
│ fac9ae08-9fde-4907…  │ 16e7fabc-35be-4e93…  │ fredy     │ Fredy       │ david       │ Hola    │ text         │ 2025-08-22 21:54:1…  │ 2025-08-22 21:54:1…  │
└──────────────────────┴──────────────────────┴───────────┴─────────────┴─────────────┴─────────┴──────────────┴──────────────────────┴──────────────────────┘
```
