import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import ChatApp from "./components/ChatApp";
import AdminLogin from "./components/AdminLogin";
import AdminDashboard from "./components/AdminDashboard";
import Services from "./components/Services";   // ✅ NEW
import Contact from "./components/Contact";     // ✅ NEW
import AdminChatLogs from "./components/AdminChatLogs";
import axios from "axios";
axios.defaults.withCredentials = true;

function App() {
  return (
    <Router>
      <Routes>

        {/* Main Chatbot Page */}
        <Route path="/" element={<ChatApp />} />

        {/* Services Page */}
        <Route path="/services" element={<Services />} />   {/* ✅ NEW */}

        {/* Contact Page */}
        <Route path="/contact" element={<Contact />} />     {/* ✅ NEW */}

        {/* Admin Pages */}
        <Route path="/admin" element={<AdminLogin />} />
        <Route path="/dashboard" element={<AdminDashboard />} />
        <Route path="/admin/logs" element={<AdminChatLogs />}/>

      </Routes>
    </Router>
  );
}

export default App;
