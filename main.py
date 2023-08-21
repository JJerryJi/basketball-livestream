from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import random
import asyncio
import gzip, csv, json, time

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
<head>
    <title>Basketball Game</title>
</head>
<body>
    <h2 id="scoreboard">Score: Team A 0 - 0 Team B</h2>
    <h1>Basketball Game Live Stream</h1>
    <ul id='updates'></ul>
    <form id="username-form">
        <input type="text" id="username-input" placeholder="Enter your username">
        <button type="submit">Join Chat</button>
    </form>
    <form id="message-form" style="display: none;">
        <input type="text" id="message-input" placeholder="Type your message">
        <input type="text" id="recipient-input" placeholder="Enter recipient's username">
        <button type="submit">Send</button>
    </form>
    <script>
        var usernameForm = document.getElementById("username-form");
        var usernameInput = document.getElementById("username-input");

        var messageForm = document.getElementById("message-form");
        var messageInput = document.getElementById("message-input");
        var recipientInput = document.getElementById("recipient-input");

        usernameForm.addEventListener("submit", function(event) {
            event.preventDefault();
            var username = usernameInput.value;
            usernameForm.style.display = "none"; // Hide the username form
            messageForm.style.display = "block"; // Show the message form

            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onopen = function() {
                ws.send(`${username}`); // Send the chosen username to the server
            };

            ws.onmessage = function(event) {
                var updates = document.getElementById('updates');
                var update = document.createElement('li');
                var content = document.createTextNode(event.data);
                update.appendChild(content);
                updates.appendChild(update);

                if (event.data.startsWith("Scores:")) {
                    document.getElementById("scoreboard").textContent = event.data;
                }
            };

            messageForm.addEventListener("submit", function(event) {
                event.preventDefault();

                var message = messageInput.value;
                var recipient = recipientInput.value;

                if (recipient) {
                    message = `/private ${recipient} ${message}`;
                }

                messageInput.value = "";
                recipientInput.value = "";
                ws.send(message);
            });
        });
    </script>
</body>
</html>
"""

class GameManager:
    def __init__(self):
        self.teams = ["Team A", "Team B"]
        self.scores = {team: 0 for team in self.teams}
        self.game_running = False
        self.connected_websockets = {}
        self.private_chats = {}

    async def simulate_game(self):
        self.game_running = True
        while self.game_running:
            await asyncio.sleep(1)
            # ... (Game simulation logic)

    def get_scores(self):
        return f"Scores: {self.teams[0]} {self.scores[self.teams[0]]} - {self.scores[self.teams[1]]} {self.teams[1]}"

    async def broadcast(self, message: str):
        for websocket in self.connected_websockets.values():
            await websocket.send_text(message)

    async def send_new_user_message(self, username: str):
        await self.broadcast(f"Welcome, {username}! You are now connected to the game.")
        await self.connected_websockets[username].send_text(f'Your username is: {username}')

    async def send_private_message(self, sender_username, recipient_username, message):
        sender_socket = self.connected_websockets.get(sender_username)
        recipient_socket = self.connected_websockets.get(recipient_username)

        if sender_socket and recipient_socket:
            chat_id = f"{sender_username}-{recipient_username}"
            self.private_chats.setdefault(chat_id, [])
            self.private_chats[chat_id].append((sender_username, message))
            await self.broadcast_private_message(chat_id, sender_socket, recipient_socket, message)
        else:
            await self.broadcast(f"{sender_username}: Private message failed, user not found.")

    async def broadcast_private_message(self, chat_id, sender_socket, recipient_socket, message):
        chat_history = self.private_chats.get(chat_id, [])
        for user_id, msg in chat_history:
            await sender_socket.send_text(f"To {chat_id.split('-')[1]}: {msg}")
            await recipient_socket.send_text(f"From {user_id}: {msg}")

manager = GameManager()

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    username = await websocket.receive_text()
    manager.connected_websockets[username] = websocket

    await manager.send_new_user_message(username)

    try:
        while True:
            # take some time to performa a request
            convert_json_takes_time()
            message = await websocket.receive_text()
            if message.startswith("/private"):
                _, recipient, private_message = message.split(" ", 2)
                await manager.send_private_message(username, recipient, private_message)
            else:
                await manager.broadcast(f"User {username}: {message}")
    except WebSocketDisconnect:
        del manager.connected_websockets[username]
        users = list(manager.connected_websockets.keys())
        await manager.broadcast(f"UpdateRecipients:{','.join(users)}")


@app.on_event("shutdown")
async def shutdown():
    manager.game_running = False


def convert_json_takes_time():
    json_output_path = "/Users/jerry/Desktop/physionet.org/files/mimiciv/2.0/icu/procedureevents.json"
    csv_file_path = "/Users/jerry/Desktop/physionet.org/files/mimiciv/2.0/icu/procedureevents.csv.gz"

    print("JSON conversion started")
    start_time = time.time()  # Record the start time

    json_data = []
    with gzip.open(csv_file_path, 'rt') as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            json_data.append(row)

    with open(json_output_path, 'w') as jsonfile:
        json.dump(json_data, jsonfile, indent=4)

    end_time = time.time()  # Record the end time
    elapsed_time = end_time - start_time
    print(f"JSON conversion completed in {elapsed_time:.2f} seconds")

    print("Conversion completed!")