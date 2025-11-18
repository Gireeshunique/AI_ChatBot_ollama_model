// server.js
const express = require("express");
const cors = require("cors");
const fs = require("fs");
const path = require("path");

const app = express();
app.use(cors());
app.use(express.json());

const PORT = 5000;

// File to store chat logs
const LOG_FILE = path.join(__dirname, "chatlogs.json");

// Helpers
const readLogs = () => {
  if (!fs.existsSync(LOG_FILE)) return [];
  const data = fs.readFileSync(LOG_FILE);
  return JSON.parse(data);
};

const saveLogs = (logs) => fs.writeFileSync(LOG_FILE, JSON.stringify(logs, null, 2));

// ------------------ Routes ------------------

// Save a new chat log
app.post("/api/chat/log", (req, res) => {
  const { question, reply, model, feature, version, feedback } = req.body;
  const logs = readLogs();
  const ts = Math.floor(Date.now() / 1000);

  logs.push({ ts, question, reply, model, feature, version, feedback: feedback || null });
  saveLogs(logs);

  res.json({ success: true, ts });
});

// Update feedback
app.post("/api/chat/feedback", (req, res) => {
  const { ts, feedback } = req.body;
  const logs = readLogs();
  const idx = logs.findIndex(l => l.ts === ts);
  if (idx !== -1) {
    logs[idx].feedback = feedback;
    saveLogs(logs);
    return res.json({ success: true });
  }
  res.status(404).json({ success: false, msg: "Log not found" });
});

// Get all logs (admin)
app.get("/api/admin/chat/logs", (req, res) => {
  const logs = readLogs();
  res.json({ logs });
});

// Chat API placeholder
app.post("/api/chat", (req, res) => {
  const { message } = req.body;
  // Fake reply for testing
  res.json({ reply: `Bot reply to: "${message}"` });
});

app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
