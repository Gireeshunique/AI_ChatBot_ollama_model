import React from "react";
import "./ChatApp.css";   // reuse same design styles

function Services() {
  return (
    <div className="page-container">
      
      {/* ---------- NAVBAR (Same as ChatApp) ---------- */}
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

        <div className="navbar-links">
          <a href="/">Home</a>
          <a href="/services" className="active-link">Services</a>
          <a href="/contact">Contact</a>
          <a href="/admin">Admin</a>
        </div>

        <div className="nav-icons">
          <span className="material-icons nav-icon bell-icon">notifications</span>
          <span className="material-icons nav-icon login-icon">account_circle</span>
        </div>
      </nav>

      {/* ---------- PAGE BODY ---------- */}
      <div className="content-wrapper">
        <h1 className="page-title">Our MSME Services</h1>
        <p className="page-subtext">
          We provide resources, guidance, and support for Micro, Small & Medium Enterprises.
        </p>

        <div className="services-grid">
          <div className="service-card">
            <h3>📘 MSME Registration</h3>
            <p>Guidance for applying and obtaining MSME Udyam Certificate.</p>
          </div>

          <div className="service-card">
            <h3>💰 Loan Assistance</h3>
            <p>Support for securing business loans under government schemes.</p>
          </div>

          <div className="service-card">
            <h3>📄 Documentation Support</h3>
            <p>Help with documentation required for new and existing MSMEs.</p>
          </div>

          <div className="service-card">
            <h3>📈 Business Growth Advisory</h3>
            <p>Consultation for expanding your business and improving productivity.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Services;
