import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";  // ✅ Correct import for your main component
import "./index.css";         // Optional, if you have it

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />   {/* ✅ Correct usage of App */}
  </React.StrictMode>
);
