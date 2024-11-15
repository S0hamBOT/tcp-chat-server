import sys
import socket
import threading
import logging
import json
import time
import os
import platform
import colorama
from datetime import datetime
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass
from colorama import Fore, Back, Style

@dataclass
class Message:
    """Represents a chat message with metadata"""
    content: str
    sender: str
    timestamp: datetime
    type: str = "normal"  # normal, system, private, error
    recipient: str = None

class ChatTheme:
    """Chat color theme and styling with customization support"""
    THEMES = {
        "default": {
            "system": Fore.YELLOW,
            "error": Fore.RED + Style.BRIGHT,
            "success": Fore.GREEN,
            "username": Fore.CYAN + Style.BRIGHT,
            "timestamp": Fore.BLUE,
            "message": Fore.WHITE,
            "private": Fore.MAGENTA,
            "command": Fore.GREEN + Style.BRIGHT,
            "header": Fore.YELLOW + Style.BRIGHT,
        },
        "dark": {
            "system": Fore.LIGHTBLUE_EX,
            "error": Fore.LIGHTRED_EX,
            "success": Fore.LIGHTGREEN_EX,
            "username": Fore.LIGHTCYAN_EX,
            "timestamp": Fore.LIGHTBLACK_EX,
            "message": Fore.LIGHTWHITE_EX,
            "private": Fore.LIGHTMAGENTA_EX,
            "command": Fore.LIGHTGREEN_EX,
            "header": Fore.LIGHTYELLOW_EX,
        }
    }
    
    def __init__(self, theme_name: str = "default"):
        self.current_theme = self.THEMES.get(theme_name, self.THEMES["default"])
        
    def get_color(self, element: str) -> str:
        return self.current_theme.get(element, Style.RESET_ALL)

class ChatClient:
    def __init__(self, host: str = "localhost", port: int = 25000):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.username = None
        self.last_active = time.time()
        self.message_history: List[Message] = []
        self.max_history = 100
        self.version = "2.1.0"
        self.theme = None
        self.command_handlers: Dict[str, Callable] = {}
        
        # Initialize colorama for Windows color support
        colorama.init()
        
        # Set up logging with more detailed configuration
        self._setup_logging()
        
        # Load user preferences if they exist
        self.preferences = self._load_preferences()
        
        # Initialize theme
        self.theme = ChatTheme(self.preferences.get("theme", "default"))
        
        # Register command handlers
        self._register_commands()

    def _setup_logging(self):
        """Configure detailed logging"""
        log_format = '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler('chat_client.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

    def _load_preferences(self) -> Dict:
        """Load user preferences from JSON file"""
        default_prefs = {
            "show_timestamps": True,
            "save_history": True,
            "notification_sound": True,
            "theme": "default",
            "max_history": 100
        }
        
        try:
            if os.path.exists('preferences.json'):
                with open('preferences.json', 'r') as f:
                    return {**default_prefs, **json.load(f)}
        except Exception as e:
            logging.warning(f"Could not load preferences: {e}")
        
        return default_prefs

    def _save_preferences(self):
        """Save user preferences to JSON file"""
        try:
            with open('preferences.json', 'w') as f:
                json.dump(self.preferences, f, indent=4)
        except Exception as e:
            logging.error(f"Could not save preferences: {e}")

    def _register_commands(self):
        """Register all available chat commands"""
        self.command_handlers = {
            '/clear': self._clear_screen,
            '/help': self._show_help,
            '/history': self._show_history,
            '/version': lambda: self._system_message(f"Client version: {self.version}"),
            '/preferences': self._show_preferences,
            '/status': self._show_status,
            '/theme': self._change_theme,
            '/export': self._export_history,
            '/filter': self._filter_history,
        }

    def display_welcome_screen(self):
        """Display a professional welcome screen"""
        os.system('cls' if platform.system() == 'Windows' else 'clear')
        header_color = self.theme.get_color('header')
        print(f"{header_color}")
        print("╔══════════════════════════════════════════╗")
        print("║            Professional PyChat            ║")
        print("║            Version {:<10}             ║".format(self.version))
        print("╚══════════════════════════════════════════╝")
        print(f"{Style.RESET_ALL}")
        print(f"{self.theme.get_color('system')}Connecting to server at {self.host}:{self.port}...{Style.RESET_ALL}\n")

    def connect(self) -> bool:
        """Connect to the chat server with timeout and retry logic"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(10)  # 10 second timeout for initial connection
                self.socket.connect((self.host, self.port))
                self.socket.settimeout(None)  # Remove timeout for regular operations
                self.running = True
                self._system_message("Successfully connected to server!")
                return True
            except socket.timeout:
                self._error_message(f"Connection timed out. Retrying... ({retry_count + 1}/{max_retries})")
                retry_count += 1
            except Exception as e:
                logging.error(f"Connection failed: {e}")
                return False
            
            if retry_count < max_retries:
                time.sleep(2)  # Wait before retrying
        
        self._error_message(f"Failed to connect after {max_retries} attempts.")
        return False

    def _create_message(self, content: str, msg_type: str = "normal", recipient: str = None) -> Message:
        """Create a new message object"""
        return Message(
            content=content,
            sender=self.username or "Unknown",
            timestamp=datetime.now(),
            type=msg_type,
            recipient=recipient
        )

    def _print_message(self, message: Message):
        """Print a formatted message"""
        if not self.preferences.get("show_timestamps", True):
            formatted = f"{self.theme.get_color(message.type)}{message.content}{Style.RESET_ALL}"
        else:
            timestamp = message.timestamp.strftime("%H:%M:%S")
            formatted = f"{self.theme.get_color('timestamp')}[{timestamp}] {self.theme.get_color(message.type)}{message.content}{Style.RESET_ALL}"
        print(formatted)

    def _system_message(self, content: str):
        """Print a system message"""
        msg = self._create_message(content, "system")
        self._print_message(msg)
        self._add_to_history(msg)

    def _error_message(self, content: str):
        """Print an error message"""
        msg = self._create_message(content, "error")
        self._print_message(msg)
        self._add_to_history(msg)

    def _add_to_history(self, message: Message):
        """Add message to history with limit checking"""
        if self.preferences.get("save_history", True):
            self.message_history.append(message)
            while len(self.message_history) > self.max_history:
                self.message_history.pop(0)

    def _handle_commands(self, message: str) -> bool:
        """Handle client-side commands"""
        parts = message.split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        if command in self.command_handlers:
            if args:
                self.command_handlers[command](*args)
            else:
                self.command_handlers[command]()
            return True
        return False

    def _clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if platform.system() == 'Windows' else 'clear')
        self._system_message("Screen cleared.")

    def _show_help(self):
        """Display help information"""
        command_color = self.theme.get_color('command')
        reset_color = Style.RESET_ALL
        
        help_text = f"""
{self.theme.get_color('header')}Available Commands:{reset_color}
{command_color}/help{reset_color} - Show this help message
{command_color}/clear{reset_color} - Clear screen
{command_color}/online{reset_color} - Show online users
{command_color}/quit{reset_color} - Leave chat
{command_color}/whisper <username> <message>{reset_color} - Send private message
{command_color}/history{reset_color} - Show message history
{command_color}/version{reset_color} - Show client version
{command_color}/preferences{reset_color} - Show user preferences
{command_color}/status{reset_color} - Show connection status
{command_color}/theme <theme_name>{reset_color} - Change color theme
{command_color}/export [filename]{reset_color} - Export chat history
{command_color}/filter <text>{reset_color} - Filter message history
{command_color}BYE{reset_color} or {command_color}bye{reset_color} - Exit application
"""
        print(help_text)

    def _show_history(self):
        """Display message history"""
        if not self.message_history:
            self._system_message("No message history available.")
            return
            
        print(f"{self.theme.get_color('header')}Message History:{Style.RESET_ALL}")
        for msg in self.message_history[-20:]:  # Show last 20 messages
            self._print_message(msg)

    def _show_preferences(self):
        """Display current user preferences"""
        print(f"{self.theme.get_color('header')}Current Preferences:{Style.RESET_ALL}")
        for key, value in self.preferences.items():
            print(f"{self.theme.get_color('command')}{key}: {self.theme.get_color('message')}{value}{Style.RESET_ALL}")

    def _show_status(self):
        """Display connection status and statistics"""
        uptime = time.time() - self.last_active
        hours, remainder = divmod(int(uptime), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        status = f"""
{self.theme.get_color('header')}Connection Status:{Style.RESET_ALL}
Server: {self.host}:{self.port}
Username: {self.username}
Connected for: {hours:02d}:{minutes:02d}:{seconds:02d}
Messages in history: {len(self.message_history)}
Client version: {self.version}
Current theme: {self.preferences.get('theme', 'default')}
"""
        print(status)

    def _change_theme(self, theme_name: str = None):
        """Change the chat theme"""
        if not theme_name:
            available_themes = ", ".join(ChatTheme.THEMES.keys())
            self._system_message(f"Available themes: {available_themes}")
            return
        
        if theme_name in ChatTheme.THEMES:
            self.theme = ChatTheme(theme_name)
            self.preferences["theme"] = theme_name
            self._save_preferences()
            self._system_message(f"Theme changed to {theme_name}")
        else:
            self._error_message(f"Theme '{theme_name}' not found")

    def _export_history(self, filename: str = None):
        """Export chat history to a file"""
        if not filename:
            filename = f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for msg in self.message_history:
                    f.write(f"[{msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] "
                           f"{msg.sender}: {msg.content}\n")
            self._system_message(f"History exported to {filename}")
        except Exception as e:
            self._error_message(f"Failed to export history: {e}")

    def _filter_history(self, filter_text: str = None):
        """Filter and display message history"""
        if not filter_text:
            self._error_message("Usage: /filter <text>")
            return
            
        filtered_messages = [
            msg for msg in self.message_history 
            if filter_text.lower() in msg.content.lower()
        ]
        
        if not filtered_messages:
            self._system_message("No matching messages found")
            return
            
        print(f"\n{self.theme.get_color('header')}Filtered Messages:{Style.RESET_ALL}")
        for msg in filtered_messages[-20:]:
            self._print_message(msg)

    def _receive_messages(self):
        """Handle incoming messages with improved error handling"""
        while self.running:
            try:
                message = self.socket.recv(2048).decode("utf8")
                if not message:
                    break
                
                msg_type = "private" if "whispered to you:" in message else "normal"
                msg = self._create_message(message, msg_type)
                
                print(f"\r", end="")  # Clear current line
                self._print_message(msg)
                self._add_to_history(msg)
                
                print("\nYou: ", end="", flush=True)
                
            except Exception as e:
                if self.running:
                    logging.error(f"Error receiving message: {e}")
                break

    def _send_messages(self):
        """Handle outgoing messages with command processing"""
        while self.running:
            try:
                message = input("\nYou: ").strip()
                
                if message.lower() in ["bye", "quit"]:
                    self._system_message("Closing the chat application...")
                    self.socket.send("/quit".encode("utf8"))
                    self.shutdown()
                    os._exit(0)
                
                if not message:
                    continue
                
                if message.startswith('/'):
                    if self._handle_commands(message):
                        continue
                
                self.socket.send(message.encode("utf8"))
                self.last_active = time.time()
                sys.stdout.write("\033[F\033[K")  # Clear previous line
                
            except Exception as e:
                if self.running:
                    logging.error(f"Error sending message: {e}")
                break

    def start(self):
        """Start the chat client with improved initialization"""
        self.display_welcome_screen()
        
        if not self.connect():
            return

        receive_thread = threading.Thread(target=self._receive_messages)
        send_thread = threading.Thread(target=self._send_messages)
        
        receive_thread.daemon = True
        send_thread.daemon = True
        
        receive_thread.start()
        send_thread.start()
        
        try:
            while receive_thread.is_alive() and send_thread.is_alive() and self.running:
                receive_thread.join(0.1)
                send_thread.join(0.1)
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        """Clean shutdown of client"""
        self.running = False
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except:
                pass
        self._save_preferences()
        logging.info("Client shutdown complete")

def main():
    client = ChatClient()
    try:
        client.start()
    except KeyboardInterrupt:
        print(f"\n{ChatTheme.SYSTEM}Closing client...{ChatTheme.RESET}")
    finally:
        client.shutdown()
        print(f"{ChatTheme.SUCCESS}You can now close the application.{ChatTheme.RESET}")

if __name__ == "__main__":
    main()