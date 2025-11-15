import React, { useState } from "react";
import axios from "axios";
import "./ChatApp.css";

function ChatMessage({ sender, text }) {
  const [feedback, setFeedback] = useState(null);
  const [showMsg, setShowMsg] = useState(false);

  const sendFeedback = async (type) => {
    setFeedback(type);
    setShowMsg(true);

    try {
      await axios.post("http://localhost:5000/api/feedback", {
        reply: text,
        feedback: type,
      });
    } catch (err) {
      console.error("Feedback error:", err);
    }

    setTimeout(() => setShowMsg(false), 2000);
  };

  return (
    <div className={`chat-message ${sender === "user" ? "user-row" : "bot-row"}`}>

      {/* BOT ICON LEFT */}
      {sender === "bot" && (
        <div className="chat-avatar">
          <span className="material-icons bot-icon">smart_toy</span>
        </div>
      )}

      {/* MESSAGE BUBBLE */}
      <div className="chat-bubble">
        <div className="chat-text">{text}</div>

        {/* FEEDBACK MESSAGE ICON */}
        {sender === "bot" && showMsg && (
          <div
            className={`feedback-label ${
              feedback === "like" ? "good" : "bad"
            }`}
          >
            <span className="material-icons feedback-icon">
              {feedback === "like" ? "check_circle" : "error_outline"}
            </span>
          </div>
        )}
      </div>

      {/* USER ICON RIGHT */}
      {sender === "user" && (
        <div className="chat-avatar">
          <span className="material-icons user-icon">person</span>
        </div>
      )}
    </div>
  );
}

export default ChatMessage;
