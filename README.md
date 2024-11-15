# tcp-server-chat

tcp-server-chat is a command-line chat application built using Python. It allows users to connect to a chat server, send and receive messages, and perform various chat-related commands.

## Features

- **Real-time Chat**: Users can send and receive messages in real-time, with the option to send private messages to specific users.
- **User Management**: The server keeps track of connected users and allows users to see who is online.
- **Command Support**: Users can use various commands, such as `/help`, `/clear`, `/history`, `/theme`, and more, to interact with the application.
- **Message History**: The client keeps a history of the messages, allowing users to view past conversations.
- **Customizable Themes**: Users can change the color theme of the chat application to their preference.
- **Logging and Error Handling**: The application includes detailed logging and robust error handling to ensure smooth operation.
- **Portable and Cross-Platform**: The application can be run on Windows, macOS, and Linux.

## Installation and Usage

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/professional-pychat.git

2. Navigate to the project directory:
   ```bash
   cd tcp-server-chat

3. Run the server:
   ```bash
   python server.py

4. In a separate terminal, run the client:
   ```bash
   python client.py

5. Follow the on-screen instructions to connect to the server, enter a username, and start chatting.


## Commands

* `/help`: Display the list of available commands.
* `/clear`: Clear the screen.
* `/online`: Show the list of online users.
* `/quit`: Leave the chat.
* `/whisper <username> <message>`: Send a private message to a specific user.
* `/history`: Display the message history.
* `/version`: Show the client version.
* `/preferences`: Display the current user preferences.
* `/status`: Show the connection status and statistics.
* `/theme <theme_name>`: Change the color theme of the chat.
* `/export [filename]`: Export the chat history to a file.
* `/filter <text>`: Filter the message history by a specific text.

## Contributing

Contributions are welcome! Please fork the repository and create a pull request to suggest changes or enhancements.
