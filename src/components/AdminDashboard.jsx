import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import "./AdminDashboard.css";

const textContent = {
  en: {
    home: "Home",
    services: "Services",
    contact: "Contact",
    admin: "Admin",
    chatLogs: "Chat Logs"
  },
};
const language = "en";

export default function AdminDashboard() {
  const navigate = useNavigate();

  const modelList = {
    gemma2: "Gemma 2B",
    phi3: "Phi 3.1 3B"
  };

  const [activeModel, setActiveModel] = useState("gemma2");

  const [models, setModels] = useState({
    gemma2: { version: "", description: "", files: [], rag: true, lora: false, info: null, loading: false, progress: 0 },
    phi3: { version: "", description: "", files: [], rag: true, lora: false, info: null, loading: false, progress: 0 },
  });

  const [versionHistory, setVersionHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // ---------------------------------------------------------
  // INIT
  // ---------------------------------------------------------
  useEffect(() => {
    let mounted = true;

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
          } catch { }
        }

        await refreshHistory();
      } catch (err) {
        console.error("Init error", err);
      }
    }

    if (mounted) init();
    return () => { mounted = false; };
  }, [navigate]);

  // ---------------------------------------------------------
  // LOAD VERSION HISTORY
  // ---------------------------------------------------------
  const refreshHistory = async () => {
    setLoadingHistory(true);
    try {
      const h = await axios.get("/api/admin/train/history");
      setVersionHistory(h.data?.versions || []);
    } catch {
      setVersionHistory([]);
    } finally {
      setLoadingHistory(false);
    }
  };

  // ---------------------------------------------------------
  // UPDATE MODEL FIELD
  // ---------------------------------------------------------
  const updateField = (model, key, value) => {
    setModels(prev => ({
      ...prev,
      [model]: { ...prev[model], [key]: value }
    }));
  };

  // ---------------------------------------------------------
  // TRAIN MODEL
  // ---------------------------------------------------------
  const trainModel = async (modelKey) => {
    const m = models[modelKey];

    if (!m.version) return alert("Version name required!");
    if (!m.files.length) return alert("Upload at least one PDF!");

    const form = new FormData();
    form.append("version", m.version);
    form.append("description", m.description);
    form.append("model_key", modelKey);
    form.append("train_rag", m.rag);
    form.append("train_lora", m.lora);

    for (let i = 0; i < m.files.length; i++) form.append("files", m.files[i]);

    try {
      updateField(modelKey, "loading", true);
      updateField(modelKey, "progress", 10);

      const res = await axios.post("/api/admin/train", form, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (p) => {
          const percent = p.total ? Math.round((p.loaded / p.total) * 60) : 30;
          updateField(modelKey, "progress", percent);
        }
      });

      updateField(modelKey, "progress", 90);

      const info = await axios.get(`/api/admin/train/info?model=${modelKey}`);
      updateField(modelKey, "info", info.data?.trained !== false ? info.data : null);

      await refreshHistory();

      updateField(modelKey, "progress", 100);
      setTimeout(() => updateField(modelKey, "progress", 0), 700);
      updateField(modelKey, "loading", false);

      alert(res.data?.message || "Trained successfully.");
    } catch (err) {
      console.error("Train error:", err);
      updateField(modelKey, "loading", false);
      updateField(modelKey, "progress", 0);
      alert("Training failed.");
    }
  };

  // ---------------------------------------------------------
  // ACTIVATE VERSION
  // ---------------------------------------------------------
  const activateVersion = async (modelKey, version) => {
    if (!window.confirm(`Activate version "${version}" for model ${modelKey}?`)) return;

    try {
      const res = await axios.post("/api/admin/activate", { model: modelKey, version });

      if (res.data?.success) {
        await refreshHistory();
        const info = await axios.get(`/api/admin/train/info?model=${modelKey}`);
        updateField(modelKey, "info", info.data?.trained !== false ? info.data : null);

        alert("Activated.");
      } else alert(res.data?.message);
    } catch {
      alert("Activation failed.");
    }
  };

  // ---------------------------------------------------------
  // DELETE VERSION (HISTORY)
  // ---------------------------------------------------------
  const deleteVersion = async (modelKey, version) => {
    if (!window.confirm(`Delete version "${version}" for model ${modelKey}?`)) return;

    try {
      const res = await axios.post("/api/admin/delete-version", { model: modelKey, version });

      if (res.data?.success) {
        await refreshHistory();

        const info = await axios.get(`/api/admin/train/info?model=${modelKey}`);
        updateField(modelKey, "info", info.data?.trained !== false ? info.data : null);

        alert("Deleted.");
      } else alert(res.data?.message);
    } catch {
      alert("Delete failed.");
    }
  };

  // ---------------------------------------------------------
  // DELETE ACTIVE VERSION
  // ---------------------------------------------------------
 const deleteActiveVersion = async (modelKey, version) => {
  if (!version) {
    alert("❌ No active version found!");
    return;
  }

  if (!window.confirm(`Delete ACTIVE version "${version}" for model ${modelKey}?`)) return;

  try {
    const res = await axios.post("/api/admin/delete-version", {
      model: modelKey,
      version: version,
    });

    if (res.data?.success) {
      // Refresh info
      const info = await axios.get(`/api/admin/train/info?model=${modelKey}`);
      updateField(modelKey, "info", info.data?.trained !== false ? info.data : null);

      await refreshHistory();
      alert("Active version deleted.");
    } else {
      alert(res.data?.message || "Delete failed.");
    }
  } catch (err) {
    console.error("Delete active version error:", err);
    alert("Delete failed.");
  }
};


  // ---------------------------------------------------------
  // UI
  // ---------------------------------------------------------
  return (
    <div className="admin-page">
      {/* NAVBAR */}
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
          <a href="/admin" className="active-nav">{textContent[language].admin}</a>
          <a href="/admin/logs">{textContent[language].chatLogs}</a>
        </div>

        <div className="nav-user-logo">👤</div>
      </nav>


      {/* MAIN */}
      <div className="admin-main">
        <div className="back-chat-wrapper">
          <button className="back-chat-btn" onClick={() => navigate("/")}>
            🔙 Back to Chat
          </button>
        </div>

        <h1 className="admin-title">🛠️ Admin Dashboard</h1>
        <p className="admin-sub">Train & Manage AI Models</p>


        {/* TABS */}
        <div className="model-tabs">
          {Object.keys(modelList).map((key) => (
            <button
              key={key}
              className={`tab-btn ${activeModel === key ? "active" : ""}`}
              onClick={() => setActiveModel(key)}
            >
              {modelList[key]}
            </button>
          ))}
        </div>


        {/* ACTIVE MODEL CARD */}
        <div className="admin-card">
          <h2 className="card-title">🤖 {modelList[activeModel]}</h2>

          {/* Inputs */}
          <label className="label">Version Name *</label>
          <input
            className="input"
            value={models[activeModel].version}
            placeholder="e.g., MSME ONE Q1 2025"
            onChange={(e) => updateField(activeModel, "version", e.target.value)}
          />

          <label className="label">Description</label>
          <textarea
            className="textarea"
            value={models[activeModel].description}
            placeholder="Short description (optional)"
            onChange={(e) => updateField(activeModel, "description", e.target.value)}
          />

          <label className="label">Upload PDF *</label>
          <input
            type="file"
            multiple
            accept=".pdf"
            onChange={(e) =>
              updateField(activeModel, "files", e.target.files)
            }
          />

          <div className="training-options">
            <label>
              <input
                type="checkbox"
                checked={models[activeModel].rag}
                onChange={() =>
                  updateField(activeModel, "rag", !models[activeModel].rag)
                }
              />
              🎯 Train RAG
            </label>

            <label>
              <input
                type="checkbox"
                checked={models[activeModel].lora}
                onChange={() =>
                  updateField(activeModel, "lora", !models[activeModel].lora)
                }
              />
              🧩 Train LoRA
            </label>
          </div>

          <div style={{ display: "flex", gap: 12, marginTop: 12 }}>
            <button className="upload-btn" onClick={() => trainModel(activeModel)}>
              🚀 {models[activeModel].loading ? "Training..." : "Upload & Train"}
            </button>

            {models[activeModel].loading && (
              <div className="progress-bar small">
                <div
                  className="progress-fill"
                  style={{ width: `${models[activeModel].progress}%` }}
                ></div>
              </div>
            )}
          </div>

          {/* ACTIVE VERSION BOX */}
          <h3 className="active-title">📌 Active Version</h3>

          {!models[activeModel].info ? (
            <p className="no-version">No trained version yet.</p>
          ) : (
            <div className="version-box">
              <p><b>📅 Trained:</b> {models[activeModel].info.timestamp}</p>
              <p>
                <b>Version:</b> {models[activeModel].info.version}{" "}
                {models[activeModel].info.active && (
                  <span className="active-pill">ACTIVE</span>
                )}
              </p>

              <p><b>Files:</b></p>
              <ul>
                {models[activeModel].info.files.map((f, i) => (
                  <li key={i}>📘 {f}</li>
                ))}
              </ul>

              {/* DELETE ACTIVE VERSION BUTTON */}
              <button
                className="small-btn danger"
                style={{ marginTop: "10px" }}
                onClick={() => deleteActiveVersion(activeModel)}
              >
                ❌ Delete Active Version
              </button>
            </div>
          )}
        </div>


        {/* VERSION HISTORY */}
        <div className="admin-card">
          <div className="flex-between">
            <h2 className="card-title">📚 Version History</h2>
            <button
              className="refresh-btn"
              onClick={refreshHistory}
              disabled={loadingHistory}
            >
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
                      📅 {v.timestamp} • Model: {v.model}{" "}
                      {v.active && (
                        <span className="active-pill">ACTIVE</span>
                      )}
                    </p>
                    <p className="vh-desc">{v.description}</p>
                  </div>

                  <div className="history-actions">
                    <button
                      className="small-btn"
                      onClick={() => activateVersion(v.model, v.version)}
                      disabled={v.active}
                    >
                      Activate
                    </button>

                    <button
                      className="small-btn danger"
                     onClick={() => deleteActiveVersion(activeModel, models[activeModel].info.version)}

                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <footer className="admin-footer">© 2025 MSME ONE — All Rights Reserved.</footer>
      </div>
    </div>
  );
}
