import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import "./AdminDashboard.css";
import "./ChatApp.css";

export default function AdminDashboard() {
  const navigate = useNavigate();

  // 3 Ollama Models
  const modelNames = {
    llama: "LLaMA 3.2",
    phi: "Phi-3",
    mistral: "Mistral",
  };

  const [models, setModels] = useState({
    llama: {
      version: "",
      description: "",
      files: [],
      rag: true,
      lora: false,
      loading: false,
      msg: "",
      info: null,
    },
    phi: {
      version: "",
      description: "",
      files: [],
      rag: true,
      lora: false,
      loading: false,
      msg: "",
      info: null,
    },
    mistral: {
      version: "",
      description: "",
      files: [],
      rag: true,
      lora: false,
      loading: false,
      msg: "",
      info: null,
    },
  });

  // Check Admin Login + Load Model Info
  useEffect(() => {
    async function init() {
      try {
        const check = await axios.get("/api/admin/check");
        if (!check.data.logged_in) navigate("/admin");

        // Load train info for each model
        for (const key of Object.keys(modelNames)) {
          const res = await axios.get(`/api/admin/train/info?model=${key}`);
          if (res.data?.trained) {
            setModels((prev) => ({
              ...prev,
              [key]: { ...prev[key], info: res.data },
            }));
          }
        }
      } catch (e) {
        console.log("Error:", e);
      }
    }
    init();
  }, []);

  const updateField = (model, field, value) => {
    setModels((prev) => ({
      ...prev,
      [model]: { ...prev[model], [field]: value },
    }));
  };

  const handleFileChange = (model, e) => {
    setModels((prev) => ({
      ...prev,
      [model]: { ...prev[model], files: e.target.files },
    }));
  };

  const toggle = (model, key) => {
    setModels((prev) => ({
      ...prev,
      [model]: { ...prev[model], [key]: !prev[model][key] },
    }));
  };

  const trainModel = async (model) => {
    const m = models[model];

    if (!m.version) return alert("Version name required!");
    if (!m.files.length) return alert("Please upload PDF files!");

    const form = new FormData();
    form.append("version", m.version);
    form.append("description", m.description);
    form.append("model_key", model);
    form.append("train_rag", m.rag);
    form.append("train_lora", m.lora);

    for (let f of m.files) form.append("files", f);

    try {
      updateField(model, "loading", true);
      updateField(model, "msg", "🚀 Training started...");

      await axios.post("/api/admin/train", form);

      updateField(model, "msg", "✅ Training complete!");
      updateField(model, "loading", false);

      const info = await axios.get(`/api/admin/train/info?model=${model}`);
      updateField(model, "info", info.data);
    } catch (err) {
      console.error(err);
      updateField(model, "msg", "❌ Training failed");
      updateField(model, "loading", false);
    }
  };

  const deleteModel = async (model) => {
    if (!window.confirm("Are you sure you want to delete this model data?"))
      return;

    try {
      await axios.post(`/api/admin/train/delete?model=${model}`);

      setModels((prev) => ({
        ...prev,
        [model]: { ...prev[model], info: null, msg: "❌ Deleted successfully" },
      }));
    } catch (err) {
      console.error(err);
      alert("Error deleting model.");
    }
  };

  return (
    <div className="admin-page">
      {/* NAVBAR */}
      <nav className="admin-navbar">
        <div className="logo-box">
          <div className="logo-circle">💼</div>
          <div>
            <div className="logo-title">MSME ONE</div>
            <div className="logo-sub">Support Center</div>
          </div>
        </div>

        <button className="back-chat-btn" onClick={() => navigate("/")}>
          Back to Chat
        </button>
      </nav>

      <div className="admin-main">
        <h1 className="admin-title">🛠️ Admin Dashboard</h1>
        <p className="admin-subtitle">Train AI models independently</p>

        {/* 3 MODEL SECTIONS */}
        {Object.keys(modelNames).map((model) => (
          <div className="admin-card" key={model}>
            <h2 className="card-title">🤖 {modelNames[model]}</h2>

            {/* VERSION */}
            <label className="label">Version Name *</label>
            <input
              type="text"
              className="input"
              placeholder="e.g., MSME ONE 2.0"
              value={models[model].version}
              onChange={(e) => updateField(model, "version", e.target.value)}
            />

            {/* DESCRIPTION */}
            <label className="label">Description</label>
            <textarea
              className="textarea"
              placeholder="Short description..."
              value={models[model].description}
              onChange={(e) =>
                updateField(model, "description", e.target.value)
              }
            ></textarea>

            {/* FILE UPLOAD */}
            <label className="label">Upload PDF *</label>
            <input
              type="file"
              multiple
              accept=".pdf"
              onChange={(e) => handleFileChange(model, e)}
            />

            {/* RAG / LORA */}
            <div className="training-options">
              <label>
                <input
                  type="checkbox"
                  checked={models[model].rag}
                  onChange={() => toggle(model, "rag")}
                />
                🎯 Train RAG
              </label>

              <label>
                <input
                  type="checkbox"
                  checked={models[model].lora}
                  onChange={() => toggle(model, "lora")}
                />
                🧩 Train LoRA
              </label>
            </div>

            {/* TRAIN BUTTON */}
            <button
              className="upload-train-btn"
              disabled={models[model].loading}
              onClick={() => trainModel(model)}
            >
              {models[model].loading ? "⏳ Training..." : "🚀 Upload & Train"}
            </button>

            {models[model].msg && (
              <p className="status-msg">{models[model].msg}</p>
            )}

            {/* ACTIVE VERSION */}
            <h3 className="active-title">📌 Active Version</h3>
            {!models[model].info ? (
              <p className="no-version">No version trained yet.</p>
            ) : (
              <>
                <p><b>📅 Trained On:</b> {models[model].info.timestamp}</p>
                <p><b>🔧 Model:</b> {models[model].info.model}</p>
                <p><b>📄 Files:</b></p>
                <ul>
                  {models[model].info.files.map((f, i) => (
                    <li key={i}>📘 {f}</li>
                  ))}
                </ul>

                <button
                  className="delete-btn"
                  onClick={() => deleteModel(model)}
                >
                  🗑️ Delete Model Data
                </button>
              </>
            )}
          </div>
        ))}

        <footer className="admin-footer">
          © {new Date().getFullYear()} MSME ONE Assistant — All Rights Reserved.
        </footer>
      </div>
    </div>
  );
}
