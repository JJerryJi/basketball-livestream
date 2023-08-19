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
    <script>
        var ws = new WebSocket("ws://localhost:8000/ws");
        ws.onmessage = function(event) {
            var updates = document.getElementById('updates')
            var update = document.createElement('li')
            var content = document.createTextNode(event.data)
            update.appendChild(content)
            updates.appendChild(update)

            if (event.data.startsWith("Scores:")){
                document.getElementById("scoreboard").textContent = event.data;
            }
        };
    </script>
</body>
</html>
"""

class GameManager:
    def __init__(self):
        self.teams = ["Team A", "Team B"]
        self.scores = {team: 0 for team in self.teams}
        self.game_running = False

    async def simulate_game(self, websocket: WebSocket):
        self.game_running = True
        while self.game_running:
            await asyncio.sleep(1)  # Simulate 1 second of game time

            scoring_chance = random.random()

            if scoring_chance < 0.5:
                scoring_team = random.choice(self.teams)
                self.scores[scoring_team] += random.randint(1, 3)
                await websocket.send_text(f"{scoring_team} scores!")

            await websocket.send_text(self.get_scores())

    def get_scores(self):
        return f"Scores: {self.teams[0]} {self.scores[self.teams[0]]} - {self.scores[self.teams[1]]} {self.teams[1]}"

manager = GameManager()

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await manager.simulate_game(websocket)

@app.on_event("shutdown")
async def shutdown():
    manager.game_running = False

