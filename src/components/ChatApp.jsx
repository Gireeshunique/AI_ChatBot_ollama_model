// ChatApp.jsx
import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import ChatMessage from "./ChatMessage.jsx";
import "./ChatApp.css";

function ChatApp() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [recording, setRecording] = useState(false);

  // feature states
  const [feature, setFeature] = useState("rag");
  const [model, setModel] = useState("ollama:gemma2");
  const [version, setVersion] = useState("default");
  const [language, setLanguage] = useState("en");

  const recorderRef = useRef(null);

  const textContent = {
    en: {
      greeting: "Hello! I'm MSME ONE Assistant. You can type or speak to ask your question.",
      placeholder: "Type your message...",
      home: "Home",
      services: "Services",
      contact: "Contact",
      admin: "Admin",
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

    setMessages(prev => [...prev, { sender: "user", text: input }]);
    const userMsg = input;
    setInput("");

    try {
      const res = await axios.post("http://localhost:5000/api/chat", {
        message: userMsg,
        lang: language,
        model,
        feature,
        version,
      });

      setMessages(prev => [...prev, { sender: "bot", text: res.data.reply }]);
    } catch (err) {
      console.error("sendMessage error:", err);
      setMessages(prev => [...prev, { sender: "bot", text: "⚠ Server not reachable." }]);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      recorderRef.current = recorder;

      const chunks = [];
      recorder.ondataavailable = e => chunks.push(e.data);

      recorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: "audio/wav" });
        const formData = new FormData();
        formData.append("file", audioBlob);
        formData.append("lang", language);
        formData.append("model", model);
        formData.append("feature", feature);
        formData.append("version", version);

        try {
          const res = await axios.post("http://localhost:5000/api/transcribe", formData, {
            headers: { "Content-Type": "multipart/form-data" }
          });

          const transcribed = res.data.text || "";
          const reply = res.data.reply || "";

          setMessages(prev => [
            ...prev,
            { sender: "user", text: transcribed || "(voice)"},
            { sender: "bot", text: reply || "No reply." },
          ]);
        } catch (err) {
          console.error("transcribe error:", err);
          alert("Voice processing failed.");
        }
      };

      recorder.start();
      setRecording(true);
      // stop automatically after 4.5s
      setTimeout(() => {
        if (recorder.state !== "inactive") {
          recorder.stop();
        }
        setRecording(false);
      }, 4500);

    } catch (err) {
      console.error("getUserMedia error:", err);
      alert("Microphone access denied.");
    }
  };

  return (
    <div className="chat-container">
      {/* ---------- NAVBAR ---------- */}
      <nav className="navbar">
        <div className="navbar-left">
          <div className="navbar-title logo-box">
            <div className="logo-circle">💼</div>
            <div>
              <div className="logo-title">MSME ONE</div>
              <div className="logo-sub">Support Center</div>
            </div>
          </div>
        </div>

        <div className="nav-links">
          <a href="/">{textContent[language].home}</a>
          <a href="/services">{textContent[language].services}</a>
          <a href="/contact">{textContent[language].contact}</a>
          <a href="/admin">{textContent[language].admin}</a>
        </div>

        <button
          className="lang-btn"
          onClick={() => setLanguage(p => (p === "en" ? "te" : "en"))}
        >
          🌐 {language === "en" ? "తెలుగు" : "English"}
        </button>

        <div className="nav-icons">
          <span className="material-icons nav-icon bell-icon">notifications</span>
          <span className="material-icons nav-icon login-icon">account_circle</span>
        </div>
      </nav>

      {/* CHAT MESSAGES */}
      <div className="chat-window">
        {messages.map((msg, i) => (
          <ChatMessage key={i} sender={msg.sender} text={msg.text} />
        ))}
      </div>

      {/* COMBINED BOX */}
      <div className="combined-box">
        {/* FEATURE BAR */}
        <div className="feature-bar">
          <button
            className={`f-btn ${feature === "lora" ? "active" : ""}`}
            onClick={() => setFeature("lora")}
          >
            Gemma 2 (LoRA)
          </button>
          <button
            className={`f-btn ${feature === "rag" ? "active" : ""}`}
            onClick={() => setFeature("rag")}
          >
            Accurate (RAG)
          </button>

          <select className="panel-select" value={model} onChange={(e) => setModel(e.target.value)}>
            <option value="ollama:gemma2">Ollama Gemma2:2B</option>
            <option value="phi3.1:3b">Phi3.1:3B</option>
          </select>

          <select className="panel-select" value={version} onChange={(e) => setVersion(e.target.value)}>
            <option value="default">Default Version</option>
            <option value="original">Original 46 PDFs</option>
            <option value="ramp">RAMP Program</option>
          </select>

          <select className="panel-select" value={language} onChange={(e) => setLanguage(e.target.value)}>
            <option value="en">English</option>
            <option value="te">Telugu</option>
          </select>
        </div>

        {/* INPUT BOX WITH MIC + SEND INSIDE */}
        <div className="input-row">
          <div className="input-box">
            <input
              type="text"
              placeholder={textContent[language].placeholder}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            />

            <span className={`material-icons mic-btn ${recording ? "recording" : ""}`} onClick={startRecording}>
              {recording ? "mic_off" : "mic"}
            </span>
            <span className="material-icons send-inside" onClick={sendMessage}>send</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ChatApp;
