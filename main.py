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

        messageForm.addEventListener("submit", function(event) {
            event.preventDefault();  // Prevent form submission

            var message = messageInput.value;
            messageInput.value = "";  // Clear the input field
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

    async def simulate_game(self):
        self.game_running = True
        while self.game_running:
            await asyncio.sleep(1)

            scoring_chance = random.random()

            if scoring_chance < 0.5:
                scoring_team = random.choice(self.teams)
                self.scores[scoring_team] += random.randint(1, 3)
                await self.broadcast(f"{scoring_team} scores!")

            await self.broadcast(self.get_scores())

    def get_scores(self):
        return f"Scores: {self.teams[0]} {self.scores[self.teams[0]]} - {self.scores[self.teams[1]]} {self.teams[1]}"

    async def broadcast(self, message: str):
        for websocket in self.connected_websockets.values():
            await websocket.send_text(message)

    async def send_new_user_message(self, websocket: WebSocket, user_id: str):
        await websocket.send_text(f"Welcome, User {user_id}! You are now connected to the game.")

manager = GameManager()

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    user_id = str(random.randint(1, 1000))
    manager.connected_websockets[user_id] = websocket

    await manager.send_new_user_message(websocket, user_id)

    try:
        while True:
            message = await websocket.receive_text()
            await manager.broadcast(f"User {user_id}: {message}")  # Broadcast user message
    except WebSocketDisconnect:
        del manager.connected_websockets[user_id]

@app.on_event("shutdown")
async def shutdown():
    manager.game_running = False
