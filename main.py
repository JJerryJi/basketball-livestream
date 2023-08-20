from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import random
import asyncio

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
    <form id="message-form">
        <input type="text" id="message-input" placeholder="Type your message">
        <input type="text" id="recipient-input" placeholder="Enter recipient's user ID">
        <button type="submit">Send</button>
    </form>
    <script>
        var ws = new WebSocket("ws://localhost:8000/ws");
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

        var messageForm = document.getElementById("message-form");
        var messageInput = document.getElementById("message-input");
        var recipientInput = document.getElementById("recipient-input");

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

    async def send_new_user_message(self, user_id: str):
        await self.broadcast(f"Welcome, User {user_id}! You are now connected to the game.")

    async def send_private_message(self, sender_id, recipient_id, message):
        sender_socket = self.connected_websockets.get(sender_id)
        recipient_socket = self.connected_websockets.get(recipient_id)

        if sender_socket and recipient_socket:
            chat_id = f"{sender_id}-{recipient_id}"
            self.private_chats.setdefault(chat_id, [])
            self.private_chats[chat_id].append((sender_id, message))
            await self.broadcast_private_message(chat_id, sender_socket, recipient_socket, message)
        else:
            await self.broadcast(f"User {sender_id}: Private message failed, user not found.")

    async def broadcast_private_message(self, chat_id, sender_socket, recipient_socket, message):
        chat_history = self.private_chats.get(chat_id, [])
        for user_id, msg in chat_history:
            await sender_socket.send_text(f"To {chat_id.split('-')[0]}: {msg}")
            await recipient_socket.send_text(f"From {user_id}: {msg}")

manager = GameManager()

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    user_id = str(random.randint(1, 1000))
    manager.connected_websockets[user_id] = websocket

    await manager.send_new_user_message(user_id)

    try:
        while True:
            message = await websocket.receive_text()
            if message.startswith("/private"):
                _, recipient, private_message = message.split(" ", 2)
                await manager.send_private_message(user_id, recipient, private_message)
            else:
                await manager.broadcast(f"User {user_id}: {message}")
    except WebSocketDisconnect:
        del manager.connected_websockets[user_id]
        users = list(manager.connected_websockets.keys())
        await manager.broadcast(f"UpdateRecipients:{','.join(users)}")

@app.on_event("shutdown")
async def shutdown():
    manager.game_running = False
