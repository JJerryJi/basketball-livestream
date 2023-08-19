import React, { useState, useEffect } from 'react';
import { Container, Typography, List, ListItem, ListItemText } from '@mui/material';

function App() {
  const [updates, setUpdates] = useState([]);
  const [scoreboard, setScoreboard] = useState("Score: Team A 0 - 0 Team B");

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');

    ws.onmessage = (event) => {
      const message = event.data;
      if (message.startsWith("Scores:")) {
          setScoreboard(message);
      }
      setUpdates(prevUpdates => [...prevUpdates, message]);
  };
  

    return () => {
      ws.close();
    };
  }, []);

  return (
    <Container maxWidth="sm">
      <Typography variant="h4" align="center" gutterBottom>
        Basketball Game Live Stream
      </Typography>
      <Typography variant="h6" align="center" gutterBottom>
        {scoreboard}
      </Typography>
      <List>
        {updates.map((update, index) => (
          <ListItem key={index}>
            <ListItemText primary={update} />
          </ListItem>
        ))}
      </List>
    </Container>
  );
}

export default App;
