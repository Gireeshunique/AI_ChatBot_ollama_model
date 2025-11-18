// AdminChatLogs.jsx
import React, { useEffect, useState } from "react";
import axios from "axios";
import "./ChatLogs.css";
import { useNavigate } from "react-router-dom";

export default function AdminChatLogs() {
  const navigate = useNavigate();
  const [logs, setLogs] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [modeFilter, setModeFilter] = useState("all");
  const [fbFilter, setFbFilter] = useState("all");
  const [loading, setLoading] = useState(false);

  const authHeader = { 
    Authorization: "Bearer " + localStorage.getItem("token")
  };

  // Load all chat logs
  const loadLogs = async () => {
    setLoading(true);
    try {
      const res = await axios.get("/api/admin/chat/logs", { headers: authHeader });
      setLogs(res.data.logs || []);
      setFiltered(res.data.logs || []);
    } catch (e) {
      console.error("Load logs error", e);
      if (e.response && e.response.status === 401) {
        navigate("/admin");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, []);

  // Apply filters for model & feedback
  useEffect(() => {
    let d = [...logs];

    if (modeFilter !== "all")
      d = d.filter(l => (l.model || "").toLowerCase() === modeFilter.toLowerCase());

    if (fbFilter !== "all") {
      if (fbFilter === "none") d = d.filter(l => !l.feedback);
      else d = d.filter(l => l.feedback === fbFilter);
    }

    setFiltered(d);
  }, [modeFilter, fbFilter, logs]);

  // Set feedback for a chat
  const setFeedback = async (ts, fb) => {
    try {
      await axios.post("/api/chat/feedback", { ts, feedback: fb }, { headers: authHeader });
      await loadLogs();
    } catch (e) {
      console.error("Feedback error", e);
      alert("Failed to set feedback");
    }
  };

  const viewDetails = (ts) => {
    navigate(`/admin/logs/${ts}`);
  };

  const goToAdmin = () => {
    navigate("/dashboard", { replace: true });
  };

  return (
    <div className="chatlogs-page">
      
      {/* Header Section */}
      <div className="top-row">
        <h1>📊 User Chat Logs</h1>

        <div className="top-buttons">
          <button onClick={loadLogs} className="refresh-btn">
            {loading ? "Refreshing..." : "Refresh"}
          </button>

          <button onClick={goToAdmin} className="back-btn">
            ← Back to Dashboard
          </button>
        </div>
      </div>

      {/* Stats Box */}
      <div className="stats-box">
        <div className="stat-card"><h2>{logs.length}</h2><p>Total Conversations</p></div>
        <div className="stat-card green"><h2>{logs.filter(l => l.feedback === "positive").length}</h2><p>Positive</p></div>
        <div className="stat-card red"><h2>{logs.filter(l => l.feedback === "negative").length}</h2><p>Negative</p></div>
        <div className="stat-card gray"><h2>{logs.filter(l => !l.feedback).length}</h2><p>No Feedback</p></div>
      </div>

      {/* Filters */}
      <div className="filters-row">
        <select value={fbFilter} onChange={e => setFbFilter(e.target.value)}>
          <option value="all">All Feedback</option>
          <option value="positive">Positive</option>
          <option value="negative">Negative</option>
          <option value="none">No Feedback</option>
        </select>

        <select value={modeFilter} onChange={e => setModeFilter(e.target.value)}>
          <option value="all">All Models</option>
          <option value="gemma2:2b">Gemma2:2B</option>
          <option value="phi3.1:3b">Phi3.1:3B</option>
        </select>
      </div>

      {/* Logs Table */}
      <table className="logs-table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Question</th>
            <th>Model</th>
            <th>Feedback</th>
            <th>Actions</th>
          </tr>
        </thead>

        <tbody>
          {filtered.map((l, i) => (
            <tr key={i}>
              <td>{new Date(l.ts * 1000).toLocaleString()}</td>
              <td style={{ maxWidth: 500 }}>{l.question}</td>
              <td>{l.model}</td>
              <td>
                {l.feedback === "positive" ? "👍" :
                 l.feedback === "negative" ? "👎" : "⚪"}
              </td>
              <td className="actions-cell">
                <button onClick={() => viewDetails(l.ts)} className="small-btn primary">Details</button>
                <button onClick={() => setFeedback(l.ts, "positive")} className="small-btn feedback-positive">👍</button>
                <button onClick={() => setFeedback(l.ts, "negative")} className="small-btn danger">👎</button>
                <button onClick={() => setFeedback(l.ts, "none")} className="small-btn clear-fb">Clear</button>
              </td>
            </tr>
          ))}

          {filtered.length === 0 && !loading && (
            <tr>
              <td colSpan="5" style={{ textAlign: 'center', padding: '20px' }}>
                No chat logs found matching the filters.
              </td>
            </tr>
          )}
        </tbody>
      </table>

    </div>
  );
}
