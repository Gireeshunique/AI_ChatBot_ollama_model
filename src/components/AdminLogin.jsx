import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "./ChatApp.css";

function AdminLogin() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleLogin = async () => {
    setError("");
    if (!username || !password) {
      setError("⚠️ Please enter both username and password.");
      return;
    }

    try {
      const res = await axios.post(
        "http://localhost:5000/api/admin/login",
        { username: username.trim(), password: password.trim() },
        { headers: { "Content-Type": "application/json" } }
      );

      if (res.data && res.data.token) {
        localStorage.setItem("token", res.data.token);
        navigate("/dashboard");
      } else if (res.data && res.data.error) {
        setError(`❌ ${res.data.error}`);
      } else {
        setError("❌ Invalid credentials");
      }
    } catch (err) {
      const msg = err.response && err.response.data && err.response.data.error
        ? err.response.data.error
        : "Server not responding";
      setError(`❌ ${msg}`);
      console.error("Login error:", err);
    }
    
  };

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

        <button className="back-btn" onClick={() => navigate("/")}>
          🔙 Back to Chat
        </button>

        <p className="login-footer">💼 MSME ONE Assistant © {new Date().getFullYear()}</p>
      </div>
    </div>
  );
}

export default AdminLogin;
