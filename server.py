# server.py
import atexit
import socket
import threading
import logging
from datetime import datetime
from typing import Dict, Optional

class ChatServer:
    def __init__(self, host: str = "", port: int = 25000):
        self.host = host
        self.port = port
        self.users: Dict[socket.socket, str] = {}
        self.addresses: Dict[socket.socket, tuple] = {}
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('chat_server.log'),
                logging.StreamHandler()
            ]
        )

    def start(self):
        """Initialize and start the chat server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            logging.info(f"Chat server started on port {self.port}")
            
            # Start connection thread
            conn_thread = threading.Thread(target=self._handle_connections)
            conn_thread.daemon = True
            conn_thread.start()
            
            return True
        except Exception as e:
            logging.error(f"Failed to start server: {e}")
            return False

    def _handle_connections(self):
        """Accept and handle incoming connections"""
        while self.running:
            try:
                client, address = self.server_socket.accept()
                self.addresses[client] = address
                logging.info(f"New connection from {address[0]}")
                
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client,)
                )
                client_thread.daemon = True
                client_thread.start()
            except Exception as e:
                if self.running:
                    logging.error(f"Connection handling error: {e}")

    def _handle_client(self, client: socket.socket):
        """Handle individual client connections"""
        address = self.addresses[client][0]
        
        try:
            username = self._get_username(client)
            self.users[client] = username
            
            self._send_message(client, f"Welcome {username}! Type /help for commands.")
            self.broadcast(f"{username} has joined the chat!")
            
            self._process_client_messages(client, username)
            
        except Exception as e:
            logging.error(f"Error handling client {address}: {e}")
        finally:
            self._remove_client(client)

    def _process_client_messages(self, client: socket.socket, username: str):
        """Process messages from a specific client"""
        while self.running:
            try:
                message = client.recv(2048).decode("utf8")
                
                if not message:
                    break
                
                if message.startswith('/'):
                    self._handle_command(client, message, username)
                else:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    self.broadcast(f"[{timestamp}] {username}: {message}")
                    
            except Exception as e:
                logging.error(f"Error processing message from {username}: {e}")
                break

    def _handle_command(self, client: socket.socket, command: str, username: str):
        """Handle client commands"""
        commands = {
            '/quit': lambda: self._handle_quit(client, username),
            '/online': lambda: self._show_online_users(client),
            '/help': lambda: self._show_help(client),
            '/whisper': lambda: self._handle_whisper(client, command, username)
        }
        
        cmd = command.split()[0]
        if cmd in commands:
            commands[cmd]()
        else:
            self._send_message(client, "Unknown command. Type /help for available commands.")

    def _handle_quit(self, client: socket.socket, username: str):
        """Handle client quit command"""
        self._send_message(client, "Goodbye!")
        self._remove_client(client)
        self.broadcast(f"{username} has left the chat.")

    def _show_online_users(self, client: socket.socket):
        """Send list of online users to client"""
        online_users = ', '.join(sorted(self.users.values()))
        self._send_message(client, f"Users online: {online_users}")

    def _show_help(self, client: socket.socket):
        """Send help message to client"""
        help_text = """
Available commands:
/help - Show this help message
/online - Show online users
/quit - Leave the chat
/whisper <username> <message> - Send private message
        """
        self._send_message(client, help_text)

    def _handle_whisper(self, client: socket.socket, command: str, sender: str):
        """Handle private messages between users"""
        try:
            _, recipient, *message_parts = command.split()
            message = ' '.join(message_parts)
            
            recipient_socket = next(
                (sock for sock, name in self.users.items() if name == recipient),
                None
            )
            
            if recipient_socket:
                self._send_message(recipient_socket, f"[PM from {sender}] {message}")
                self._send_message(client, f"[PM to {recipient}] {message}")
            else:
                self._send_message(client, f"User {recipient} is not online.")
        except ValueError:
            self._send_message(client, "Usage: /whisper <username> <message>")

    def _get_username(self, client: socket.socket) -> str:
        """Get unique username from client"""
        while True:
            self._send_message(client, "Enter your username:")
            username = client.recv(2048).decode("utf8").strip()
            
            if username and username not in self.users.values():
                return username
            
            self._send_message(client, "Username already taken or invalid. Try again.")

    def _remove_client(self, client: socket.socket):
        """Remove client from server"""
        if client in self.users:
            del self.users[client]
        if client in self.addresses:
            del self.addresses[client]
        try:
            client.close()
        except:
            pass

    def _send_message(self, client: socket.socket, message: str):
        """Send message to specific client"""
        try:
            client.send(message.encode("utf8"))
        except Exception as e:
            logging.error(f"Error sending message to client: {e}")

    def broadcast(self, message: str, exclude: socket.socket = None):
        """Broadcast message to all clients except excluded one"""
        for client in list(self.users.keys()):
            if client != exclude:
                self._send_message(client, message)

    def shutdown(self):
        """Shutdown the server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        
        for client in list(self.users.keys()):
            self._remove_client(client)
        
        logging.info("Server shutdown complete")

def main():
    server = ChatServer()
    atexit.register(server.shutdown)
    
    if server.start():
        try:
            while True:
                # Keep main thread alive
                pass
        except KeyboardInterrupt:
            logging.info("Server shutdown initiated...")
            server.shutdown()

if __name__ == "__main__":
    main()

