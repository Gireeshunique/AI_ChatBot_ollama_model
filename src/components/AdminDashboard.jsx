import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import "./AdminDashboard.css";

export default function AdminDashboard() {
  const navigate = useNavigate();

  // ✔ Added LLaMA 3.1 Model here
  const modelList = {
    gemini: "Gemini-2.5-flash",
    ollama: "Ollama (Gemma 2B)",
    llama3: "Ollama (LLaMA 3.1 - 8B)"
  };

  const [activeModel, setActiveModel] = useState("gemini");

  const [models, setModels] = useState({
    gemini: { version: "", description: "", files: [], rag: true, lora: false, info: null, loading: false, progress: 0 },
    ollama: { version: "", description: "", files: [], rag: true, lora: false, info: null, loading: false, progress: 0 },
    llama3: { version: "", description: "", files: [], rag: true, lora: false, info: null, loading: false, progress: 0 },
  });

  const [versionHistory, setVersionHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  useEffect(() => {
    async function init() {
      try {
        const login = await axios.get("/api/admin/check");
        if (!login.data.logged_in) {
          navigate("/admin");
          return;
        }

        for (const key of Object.keys(modelList)) {
          try {
            const info = await axios.get(`/api/admin/train/info?model=${key}`);
            if (info.data && info.data.trained !== false) {
              setModels(prev => ({ ...prev, [key]: { ...prev[key], info: info.data } }));
            }
          } catch (e) {}
        }

        await refreshHistory();
      } catch (err) {
        console.error("Init error", err);
      }
    }
    init();
  }, []);

  const refreshHistory = async () => {
    setLoadingHistory(true);
    try {
      const h = await axios.get("/api/admin/train/history");
      setVersionHistory(h.data?.versions || []);
    } catch (e) {
      setVersionHistory([]);
    } finally {
      setLoadingHistory(false);
    }
  };

  const updateField = (model, key, value) => {
    setModels(prev => ({ ...prev, [model]: { ...prev[model], [key]: value } }));
  };

  const trainModel = async modelKey => {
    const m = models[modelKey];
    if (!m.version) return alert("Version name required!");
    if (!m.files.length) return alert("Upload at least one PDF!");

    const form = new FormData();
    form.append("version", m.version);
    form.append("description", m.description);
    form.append("model_key", modelKey);
    form.append("train_rag", m.rag);
    form.append("train_lora", m.lora);

    for (let i = 0; i < m.files.length; i++) {
      form.append("files", m.files[i]);
    }

    try {
      updateField(modelKey, "loading", true);
      updateField(modelKey, "progress", 10);

      const res = await axios.post("/api/admin/train", form, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: p => {
          const percent = p.total ? Math.round((p.loaded / p.total) * 60) : 30;
          updateField(modelKey, "progress", percent);
        }
      });

      updateField(modelKey, "progress", 90);

      const info = await axios.get(`/api/admin/train/info?model=${modelKey}`);
      if (info.data && info.data.trained !== false) {
        updateField(modelKey, "info", info.data);
      }

      await refreshHistory();

      updateField(modelKey, "progress", 100);
      setTimeout(() => updateField(modelKey, "progress", 0), 700);
      updateField(modelKey, "loading", false);

      alert(res.data?.message || "Trained successfully.");
    } catch (err) {
      console.error("Train error", err);
      updateField(modelKey, "loading", false);
      updateField(modelKey, "progress", 0);
      alert("Training failed.");
    }
  };

  const activateVersion = async (modelKey, version) => {
    if (!window.confirm(`Activate version "${version}" for model ${modelKey}?`))
      return;

    try {
      const res = await axios.post("/api/admin/activate", { model: modelKey, version });
      if (res.data?.success) {
        await refreshHistory();
        const info = await axios.get(`/api/admin/train/info?model=${modelKey}`);
        updateField(modelKey, "info", info.data && info.data.trained !== false ? info.data : null);
        alert("Activated.");
      } else alert(res.data?.message);
    } catch (e) {
      alert("Activation failed.");
    }
  };

  const deleteVersion = async (modelKey, version) => {
    if (!window.confirm(`Delete version "${version}" for model ${modelKey}?`))
      return;

    try {
      const res = await axios.post("/api/admin/delete-version", { model: modelKey, version });
      if (res.data?.success) {
        await refreshHistory();
        const info = await axios.get(`/api/admin/train/info?model=${modelKey}`);
        updateField(modelKey, "info", info.data && info.data.trained !== false ? info.data : null);
        alert("Deleted.");
      } else alert(res.data?.message);
    } catch (e) {
      alert("Delete failed.");
    }
  };

  const modelLabel = key => modelList[key] || key;

  return (
    <div className="admin-page">
      <nav className="admin-navbar">
        <div className="logo-box">
          <div className="logo-circle">💼</div>
          <div>
            <div className="logo-title">MSME ONE</div>
            <div className="logo-sub">Support Center</div>
          </div>
        </div>
      </nav>

      <div className="admin-main">

        <div className="back-chat-wrapper">
          <button className="back-chat-btn" onClick={() => navigate("/")}>🔙 Back to Chat</button>
        </div>

        <h1 className="admin-title">🛠️ Admin Dashboard</h1>
        <p className="admin-sub">Train & Manage AI Models</p>

        {/* Model Tabs */}
        <div className="model-tabs">
          {Object.keys(modelList).map(key => (
            <button
              key={key}
              className={`tab-btn ${activeModel === key ? "active" : ""}`}
              onClick={() => setActiveModel(key)}
            >
              {modelList[key]}
            </button>
          ))}
        </div>

        {/* Active Model Card */}
        <div className="admin-card">
          <h2 className="card-title">🤖 {modelLabel(activeModel)}</h2>

          <label className="label">Version Name *</label>
          <input
            className="input"
            value={models[activeModel].version}
            placeholder="e.g., MSME ONE Q1 2025"
            onChange={e => updateField(activeModel, "version", e.target.value)}
          />

          <label className="label">Description</label>
          <textarea
            className="textarea"
            value={models[activeModel].description}
            placeholder="Short description (optional)"
            onChange={e => updateField(activeModel, "description", e.target.value)}
          />

          <label className="label">Upload PDF *</label>
          <input
            type="file"
            multiple
            accept=".pdf"
            onChange={e => updateField(activeModel, "files", e.target.files)}
          />

          <div className="training-options">
            <label><input type="checkbox"
              checked={models[activeModel].rag}
              onChange={() => updateField(activeModel, "rag", !models[activeModel].rag)}
            /> 🎯 Train RAG</label>

            <label><input type="checkbox"
              checked={models[activeModel].lora}
              onChange={() => updateField(activeModel, "lora", !models[activeModel].lora)}
            /> 🧩 Train LoRA</label>
          </div>

          <div style={{ display: "flex", gap: 12, alignItems: "center", marginTop: 12 }}>
            <button className="upload-btn" onClick={() => trainModel(activeModel)}>
              🚀 {models[activeModel].loading ? "Training..." : "Upload & Train"}
            </button>

            {models[activeModel].loading && (
              <div className="progress-bar small">
                <div className="progress-fill" style={{ width: `${models[activeModel].progress}%` }}></div>
              </div>
            )}
          </div>

          <h3 className="active-title">📌 Active Version</h3>
          {!models[activeModel].info ? (
            <p className="no-version">No trained version yet.</p>
          ) : (
            <div className="version-box">
              <p><b>📅 Trained:</b> {models[activeModel].info.timestamp}</p>
              <p>
                <b>Version:</b> {models[activeModel].info.version}
                {models[activeModel].info.active ? <span className="active-pill">ACTIVE</span> : null}
              </p>
              <p><b>Files:</b></p>
              <ul>
                {models[activeModel].info.files.map((f, i) => <li key={i}>📘 {f}</li>)}
              </ul>
            </div>
          )}
        </div>

        {/* History */}
        <div className="admin-card">
          <div className="flex-between">
            <h2 className="card-title">📚 Version History</h2>
            <button className="refresh-btn" onClick={refreshHistory} disabled={loadingHistory}>
              {loadingHistory ? "Refreshing..." : "Refresh"}
            </button>
          </div>

          {versionHistory.length === 0 ? (
            <p className="no-version">No previous versions.</p>
          ) : (
            <div className="history-list">
              {versionHistory.map((v, i) => (
                <div key={i} className="history-row">
                  <div className="history-meta">
                    <h4 className="vh-title">{v.version}</h4>
                    <p className="vh-date">
                      📅 {v.timestamp} • Model: {v.model}
                      {v.active ? <span className="active-pill">ACTIVE</span> : null}
                    </p>
                    <p className="vh-desc">{v.description}</p>
                  </div>

                  <div className="history-actions">
                    <button className="small-btn" onClick={() => activateVersion(v.model, v.version)} disabled={v.active}>
                      Activate
                    </button>
                    <button className="small-btn danger" onClick={() => deleteVersion(v.model, v.version)}>
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <footer className="admin-footer">
          © 2025 MSME ONE — All Rights Reserved.
        </footer>

      </div>
    </div>
  );
}
