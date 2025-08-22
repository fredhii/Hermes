import os
import time
import json
import uuid
import threading
from datetime import datetime
import paho.mqtt.client as mqtt
import psycopg2
from psycopg2 import sql

# --- Configuration from Environment Variables ---
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "chat/messages")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_DB = os.getenv("POSTGRES_DB", "public")
POSTGRES_USER = os.getenv("POSTGRES_USER", "dbowner")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "uX3_YnF3y485NziMN6xW")

# Chat configuration
CHAT_USER_ID = os.getenv("CHAT_USER_ID", "david")
CHAT_USER_NAME = os.getenv("CHAT_USER_NAME", "David")

class ChatSubscriber:
    def __init__(self):
        self.client = None
        self.db_conn = None
        self.message_history = []
        self.running = True
        
    def get_db_connection(self):
        """Establishes a connection to the PostgreSQL database with retries."""
        conn = None
        while conn is None:
            try:
                conn = psycopg2.connect(
                    host=POSTGRES_HOST,
                    dbname=POSTGRES_DB,
                    user=POSTGRES_USER,
                    password=POSTGRES_PASSWORD
                )
                print("✅ Database connection successful!")
            except psycopg2.OperationalError as e:
                print(f"❌ Database connection failed: {e}. Retrying in 5 seconds...")
                time.sleep(5)
        return conn

    def setup_database(self, conn):
        """Creates the necessary tables for chat functionality."""
        with conn.cursor() as cur:
            # Messages table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
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
            """)
            
            # Message status table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS message_status (
                    id SERIAL PRIMARY KEY,
                    message_id VARCHAR(255) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    user_id VARCHAR(100) NOT NULL,
                    FOREIGN KEY (message_id) REFERENCES chat_messages(message_id) ON DELETE CASCADE
                );
            """)
            
            # Create indexes for better performance
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_messages_sender_id ON chat_messages(sender_id);
                CREATE INDEX IF NOT EXISTS idx_chat_messages_receiver_id ON chat_messages(receiver_id);
                CREATE INDEX IF NOT EXISTS idx_message_status_message_id ON message_status(message_id);
                CREATE INDEX IF NOT EXISTS idx_message_status_user_id ON message_status(user_id);
            """)
            
            conn.commit()
            print("📖 Chat database tables are ready.")

    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the MQTT broker."""
        if rc == 0:
            print("✅ Connected to MQTT Broker!")
            # Subscribe to general chat topic and user-specific topic
            client.subscribe(MQTT_TOPIC)
            client.subscribe(f"{MQTT_TOPIC}/{CHAT_USER_ID}")
            print(f"👂 Subscribed to topics: {MQTT_TOPIC}, {MQTT_TOPIC}/{CHAT_USER_ID}")
        else:
            print(f"❌ Failed to connect to MQTT Broker, return code {rc}\n")

    def on_message(self, client, userdata, msg):
        """Callback for when a message is received from the MQTT broker."""
        try:
            payload = msg.payload.decode()
            print(f"📩 Received message on topic '{msg.topic}': {payload}")
            
            data = json.loads(payload)
            message_type = data.get("type", "message")
            
            if message_type == "message":
                self.handle_chat_message(data)
            elif message_type == "status":
                self.handle_status_update(data)
            elif message_type == "typing":
                self.handle_typing_indicator(data)
                
        except json.JSONDecodeError:
            print(f"⚠️ Could not decode JSON from payload: {msg.payload.decode()}")
        except Exception as error:
            print(f"🔥 Error processing message: {error}")

    def handle_chat_message(self, data):
        """Handle incoming chat messages."""
        message_id = data.get("message_id")
        sender_id = data.get("sender_id")
        sender_name = data.get("sender_name")
        receiver_id = data.get("receiver_id")
        content = data.get("content")
        message_type = data.get("message_type", "text")
        
        # Only process messages intended for this user or broadcast messages
        if receiver_id != CHAT_USER_ID and receiver_id != "all":
            return
            
        # Store message in database
        with self.db_conn.cursor() as cur:
            cur.execute("""
                INSERT INTO chat_messages (message_id, sender_id, sender_name, receiver_id, content, message_type)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (message_id) DO NOTHING
            """, [message_id, sender_id, sender_name, receiver_id, content, message_type])
            
            # Add status: received by server
            cur.execute("""
                INSERT INTO message_status (message_id, status, user_id)
                VALUES (%s, %s, %s)
            """, [message_id, "received_by_server", CHAT_USER_ID])
            
            self.db_conn.commit()
        
        # Display message
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n💬 [{timestamp}] {sender_name}: {content}")
        
        # Send read receipt after a short delay (simulating user reading)
        threading.Timer(2.0, self.send_read_receipt, args=[message_id, sender_id]).start()
        
        # Add to local history
        self.message_history.append({
            "message_id": message_id,
            "sender_id": sender_id,
            "sender_name": sender_name,
            "content": content,
            "timestamp": timestamp,
            "status": "received"
        })

    def handle_status_update(self, data):
        """Handle message status updates."""
        message_id = data.get("message_id")
        status = data.get("status")
        user_id = data.get("user_id")
        
        # Update status in database
        with self.db_conn.cursor() as cur:
            cur.execute("""
                INSERT INTO message_status (message_id, status, user_id)
                VALUES (%s, %s, %s)
            """, [message_id, status, user_id])
            self.db_conn.commit()
        
        # Display status update
        status_emoji = {
            "sent": "📤",
            "received_by_server": "✅",
            "delivered": "📥",
            "read": "👁️"
        }
        emoji = status_emoji.get(status, "📊")
        print(f"{emoji} Message {message_id[:8]}... {status} by {user_id}")

    def handle_typing_indicator(self, data):
        """Handle typing indicators."""
        sender_id = data.get("sender_id")
        sender_name = data.get("sender_name")
        is_typing = data.get("is_typing", False)
        
        if is_typing:
            print(f"✍️ {sender_name} is typing...")
        else:
            print(f"   {sender_name} stopped typing")

    def send_read_receipt(self, message_id, sender_id):
        """Send read receipt for a message."""
        status_data = {
            "type": "status",
            "message_id": message_id,
            "status": "read",
            "user_id": CHAT_USER_ID,
            "timestamp": datetime.now().isoformat()
        }
        
        # Publish to sender's topic
        topic = f"{MQTT_TOPIC}/{sender_id}"
        self.client.publish(topic, json.dumps(status_data))
        print(f"👁️ Sent read receipt for message {message_id[:8]}...")

    def send_message(self, receiver_id, content, message_type="text"):
        """Send a chat message."""
        message_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        message_data = {
            "type": "message",
            "message_id": message_id,
            "sender_id": CHAT_USER_ID,
            "sender_name": CHAT_USER_NAME,
            "receiver_id": receiver_id,
            "content": content,
            "message_type": message_type,
            "timestamp": timestamp
        }
        
        # Publish to receiver's topic
        topic = f"{MQTT_TOPIC}/{receiver_id}"
        self.client.publish(topic, json.dumps(message_data))
        
        # Also publish to general topic for logging
        self.client.publish(MQTT_TOPIC, json.dumps(message_data))
        
        # Store in database
        with self.db_conn.cursor() as cur:
            cur.execute("""
                INSERT INTO chat_messages (message_id, sender_id, sender_name, receiver_id, content, message_type)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [message_id, CHAT_USER_ID, CHAT_USER_NAME, receiver_id, content, message_type])
            
            # Add sent status
            cur.execute("""
                INSERT INTO message_status (message_id, status, user_id)
                VALUES (%s, %s, %s)
            """, [message_id, "sent", CHAT_USER_ID])
            
            self.db_conn.commit()
        
        print(f"📤 Message sent: {content}")
        return message_id

    def send_typing_indicator(self, receiver_id, is_typing=True):
        """Send typing indicator."""
        typing_data = {
            "type": "typing",
            "sender_id": CHAT_USER_ID,
            "sender_name": CHAT_USER_NAME,
            "receiver_id": receiver_id,
            "is_typing": is_typing,
            "timestamp": datetime.now().isoformat()
        }
        
        topic = f"{MQTT_TOPIC}/{receiver_id}"
        self.client.publish(topic, json.dumps(typing_data))

    def get_message_history(self, limit=50):
        """Retrieve message history from database."""
        with self.db_conn.cursor() as cur:
            cur.execute("""
                SELECT cm.*, ms.status, ms.timestamp as status_timestamp
                FROM chat_messages cm
                LEFT JOIN message_status ms ON cm.message_id = ms.message_id
                WHERE cm.sender_id = %s OR cm.receiver_id = %s
                ORDER BY cm.created_at DESC
                LIMIT %s
            """, [CHAT_USER_ID, CHAT_USER_ID, limit])
            
            return cur.fetchall()

    def display_help(self):
        """Display available commands."""
        print("\n" + "="*50)
        print("💬 CHAT COMMANDS")
        print("="*50)
        print("send <user_id> <message>  - Send message to user")
        print("broadcast <message>       - Send message to all users")
        print("history [limit]           - Show message history")
        print("typing <user_id>          - Send typing indicator")
        print("help                      - Show this help")
        print("quit                      - Exit chat")
        print("="*50)

    def start_chat_interface(self):
        """Start the interactive chat interface."""
        print(f"\n🎉 Welcome to the chat, {CHAT_USER_NAME}!")
        print(f"Your ID: {CHAT_USER_ID}")
        self.display_help()
        
        while self.running:
            try:
                user_input = input(f"\n[{CHAT_USER_NAME}] ").strip()
                
                if not user_input:
                    continue
                    
                parts = user_input.split(' ', 2)
                command = parts[0].lower()
                
                if command == "send" and len(parts) >= 3:
                    receiver_id = parts[1]
                    message = parts[2]
                    self.send_message(receiver_id, message)
                    
                elif command == "broadcast" and len(parts) >= 2:
                    message = parts[1]
                    self.send_message("all", message)
                    
                elif command == "history":
                    limit = int(parts[1]) if len(parts) > 1 else 10
                    history = self.get_message_history(limit)
                    print(f"\n📚 Last {len(history)} messages:")
                    for msg in reversed(history):
                        print(f"[{msg[8]}] {msg[3]}: {msg[5]}")
                        
                elif command == "typing" and len(parts) >= 2:
                    receiver_id = parts[1]
                    self.send_typing_indicator(receiver_id, True)
                    threading.Timer(3.0, self.send_typing_indicator, args=[receiver_id, False]).start()
                    
                elif command == "help":
                    self.display_help()
                    
                elif command == "quit":
                    self.running = False
                    print("👋 Goodbye!")
                    break
                    
                else:
                    print("❌ Invalid command. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                self.running = False
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def run(self):
        """Main method to run the chat subscriber."""
        # 1. Establish database connection
        self.db_conn = self.get_db_connection()
        self.setup_database(self.db_conn)

        # 2. Setup MQTT Client
        self.client = mqtt.Client(client_id=f"chat-subscriber-{CHAT_USER_ID}")
        self.client.user_data_set({'db_conn': self.db_conn})

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        # 3. Connect to Broker and start the loop
        try:
            print("⏳ Connecting to MQTT Broker...")
            self.client.connect(MQTT_BROKER_HOST, 1883, 60)
            
            # Start MQTT loop in a separate thread
            mqtt_thread = threading.Thread(target=self.client.loop_forever)
            mqtt_thread.daemon = True
            mqtt_thread.start()
            
            # Start chat interface
            self.start_chat_interface()
            
        except Exception as e:
            print(f"🚨 Could not start MQTT client: {e}")
        finally:
            if self.db_conn:
                self.db_conn.close()
                print("🔌 Database connection closed.")

if __name__ == '__main__':
    chat_subscriber = ChatSubscriber()
    chat_subscriber.run()
