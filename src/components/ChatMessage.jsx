import React, { useState } from "react";
import axios from "axios";
import "./ChatApp.css";

function ChatMessage({ sender, text, ts }) {
  const [feedback, setFeedback] = useState(null);
  const [showMsg, setShowMsg] = useState(false);
  const [displayMsg, setDisplayMsg] = useState("");

  const sendFeedback = async (type) => {
    setFeedback(type);
    setShowMsg(true);

    setDisplayMsg(type === "like" ? "Thanks! 👍" : "We'll improve 👎");

    try {
      await axios.post(
        "http://localhost:5000/api/chat/feedback",
        {
          ts,
          feedback: type === "like" ? "positive" : "negative"
        },
        {
          withCredentials: true   // ✅ Correct place
        }
      );
    } catch (err) {
      console.error("Feedback error:", err);
      setDisplayMsg("Failed to send feedback.");
    }

    setTimeout(() => setShowMsg(false), 2000);
  };

  return (
    <div
      className={`chat-message ${
        sender === "user" ? "user-row" : "bot-row"
      }`}
    >
      {sender === "bot" && (
        <div className="chat-avatar">
          <span className="material-icons bot-icon">smart_toy</span>
        </div>
      )}

      <div className="chat-bubble">
        <div className="chat-text">{text}</div>

        {sender === "bot" && (
          <div className="feedback-buttons">
            <span
              className={`material-icons feedback-btn ${
                feedback === "like" ? "selected" : ""
              }`}
              onClick={() => sendFeedback("like")}
            >
              thumb_up
            </span>

            <span
              className={`material-icons feedback-btn ${
                feedback === "dislike" ? "selected" : ""
              }`}
              onClick={() => sendFeedback("dislike")}
            >
              thumb_down
            </span>
          </div>
        )}

        {sender === "bot" && showMsg && (
          <div
            className={`feedback-label ${
              feedback === "like" ? "good" : "bad"
            }`}
          >
            <span className="material-icons feedback-icon">
              {feedback === "like" ? "check_circle" : "error_outline"}
            </span>
            <span className="feedback-text">{displayMsg}</span>
          </div>
        )}
      </div>

      {sender === "user" && (
        <div className="chat-avatar">
          <span className="material-icons user-icon">person</span>
        </div>
      )}
    </div>
  );
}

export default ChatMessage;
