import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "./ChatApp.css";
//import "./AdminLogin.css";


function AdminLogin() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  // ---------------- LOGIN HANDLER ----------------
  const handleLogin = async () => {
    if (!username || !password) {
      setError("⚠️ Please enter both username and password.");
      return;
    }
    try {
      const res = await axios.post("/api/admin/login", { username, password });
      if (res.data.success) {
        alert("✅ Login successful!");
        navigate("/dashboard");
      } else setError("❌ Invalid credentials");
    } catch (err) {
      console.error(err);
      setError("⚠️ Server not responding. Please try again.");
    }
  };

  // ---------------- RETURN JSX ----------------
  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h2>🔐 Admin Login</h2>
          <p>Access your MSME ONE Assistant Dashboard</p>
        </div>

        <div className="login-inputs">
          <input
            type="text"
            placeholder="👤 Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <input
            type="password"
            placeholder="🔒 Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        <button className="login-btn" onClick={handleLogin}>
          🚀 Login
        </button>

        {error && <p className="error-text">{error}</p>}

        {/* 🔙 Back to Chat Button */}
        <button
          className="back-btn"
          onClick={() => navigate("/")}
          style={{ marginTop: "10px" }}
        >
          🔙 Back to Chat
        </button>

        <p className="login-footer">
          💼 MSME ONE Assistant © {new Date().getFullYear()}
        </p>
      </div>
    </div>
  );
}

export default AdminLogin;
