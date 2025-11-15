import React, { useState, useEffect } from "react";
import axios from "axios";
import ChatMessage from "./ChatMessage.jsx";
import "./ChatApp.css";

function ChatApp() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [recording, setRecording] = useState(false);
  const [language, setLanguage] = useState("en");

  const textContent = {
    en: {
      greeting: "Hello! I am MSME ONE Assistant. You can type or speak to ask your question.",
      placeholder: "Type your message...",
      home: "Home",
      services: "Services",
      contact: "Contact",
      admin: "Admin",
      serverError: "⚠️ Server not reachable.",
      voiceDenied: "Microphone access denied.",
      voiceFail: "Voice processing failed.",
    },
    te: {
      greeting: "హలో! నేను ఎంఎస్ఎంఈ వన్ సహాయకుడు.",
      placeholder: "మీ సందేశాన్ని టైప్ చేయండి...",
      home: "హోమ్",
      services: "సేవలు",
      contact: "సంప్రదించండి",
      admin: "అడ్మిన్",
    },
  };

  useEffect(() => {
    setMessages([{ sender: "bot", text: textContent[language].greeting }]);
  }, [language]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = input;

    setMessages((prev) => [...prev, { sender: "user", text: userMsg }]);
    setInput("");

    try {
      const res = await axios.post("http://localhost:5000/api/chat", {
        message: userMsg,
        lang: language,
        user_id: "guest1",
      });

      setMessages((prev) => [...prev, { sender: "bot", text: res.data.reply }]);
    } catch {
      setMessages((prev) => [...prev, { sender: "bot", text: textContent[language].serverError }]);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];

      recorder.ondataavailable = (e) => chunks.push(e.data);
      recorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: "audio/wav" });
        const formData = new FormData();
        formData.append("file", audioBlob, "voice.wav");

        try {
          const res = await axios.post("http://localhost:5000/api/transcribe", formData);
          const { text, reply } = res.data;

          setMessages((prev) => [
            ...prev,
            { sender: "user", text },
            { sender: "bot", text: reply },
          ]);
        } catch {
          alert(textContent[language].voiceFail);
        }
      };

      recorder.start();
      setRecording(true);

      setTimeout(() => {
        recorder.stop();
        setRecording(false);
      }, 4500);
    } catch {
      alert(textContent[language].voiceDenied);
    }
  };

  return (
    <div className="chat-container">
      
      {/* ---------- NAV BAR ---------- */}
      <nav className="navbar">
        <div className="navbar-left">
          <div className="navbar-title logo-box">
            <div className="logo-circle">✨</div>
            <div>
              <div className="logo-title">MSME ONE</div>
              <div className="logo-sub">Support Center</div>
            </div>
          </div>
        </div>

        <div className="navbar-links">
          <a href="/">{textContent[language].home}</a>
          <a href="/services">{textContent[language].services}</a>
          <a href="/contact">{textContent[language].contact}</a>
          <a href="/admin">{textContent[language].admin}</a>
        </div>
        
          <button
            className="lang-toggle"
            onClick={() => setLanguage((p) => (p === "en" ? "te" : "en"))}
          >
            {language === "en" ? "🌐 తెలుగు" : "🌐 English"}
          </button>

        <div className="nav-icons">
          <span className="material-icons bell-icon">notifications</span>
          <span className="material-icons login-icon">account_circle</span>

        </div>
      </nav>

      {/* ---------- CHAT WINDOW ---------- */}
      <div className="chat-window">
        {messages.map((msg, i) => (
          <ChatMessage key={i} sender={msg.sender} text={msg.text} />
        ))}
      </div>

      {/* ---------- INPUT BAR ---------- */}
      <div className="chat-input">

        <div className="input-wrapper">
          <input
            type="text"
            placeholder={textContent[language].placeholder}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          />

          <button
            className={`mic-inside ${recording ? "recording" : ""}`}
            onClick={startRecording}
          >
            <span className="material-icons">
              {recording ? "mic_none" : "mic"}
            </span>
          </button>
        </div>

        <button className="send-button" onClick={sendMessage}>
          <span className="material-icons">send</span>
        </button>
      </div>
    </div>
  );
}

export default ChatApp;
