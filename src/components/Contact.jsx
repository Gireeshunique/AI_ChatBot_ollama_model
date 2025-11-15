import React from "react";
import "./ChatApp.css";

function Contact() {
  return (
    <div className="page-container">
      
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

        <div className="navbar-links">
          <a href="/">Home</a>
          <a href="/services">Services</a>
          <a href="/contact" className="active-link">Contact</a>
          <a href="/admin">Admin</a>
        </div>

        <div className="nav-icons">
          <span className="material-icons nav-icon bell-icon">notifications</span>
          <span className="material-icons nav-icon login-icon">account_circle</span>
        </div>
      </nav>

      {/* ---------- CONTACT PAGE ---------- */}
      <div className="content-wrapper fade-in">

        {/* Header */}
        <div className="contact-header">
          <h1 className="page-title">Contact MSME Support</h1>
          <p className="page-subtext">
            Get help for MSME registration, schemes, loans, documentation & business growth.
          </p>
        </div>

        {/* Main Contact Layout */}
        <div className="contact-grid">

          {/* Phone Section */}
          <div className="contact-box">
            <div className="contact-icon-box">
              <span className="material-icons contact-big-icon">call</span>
            </div>
            <h3 className="contact-title">Phone Support</h3>
            <p><strong>General Helpline:</strong> 1800-112-111</p>
            <p><strong>Udyam Registration:</strong> 14411</p>
            <p><strong>Sampark Placement Cell:</strong> +91-11-23063800</p>
          </div>

          {/* Email Section */}
          <div className="contact-box">
            <div className="contact-icon-box">
              <span className="material-icons contact-big-icon">email</span>
            </div>
            <h3 className="contact-title">Email Support</h3>
            <p><strong>General Queries:</strong> support-msme@gov.in</p>
            <p><strong>Udyam Registration:</strong> udyamregistration@msme.gov.in</p>
            <p><strong>Grievances:</strong> grievance-msme@gov.in</p>
          </div>

          {/* Address */}
          <div className="contact-box">
            <div className="contact-icon-box">
              <span className="material-icons contact-big-icon">location_on</span>
            </div>
            <h3 className="contact-title">Office Address</h3>
            <p>Ministry of MSME</p>
            <p>Government of India</p>
            <p>Udyog Bhawan, Rafi Marg</p>
            <p>New Delhi – 110011</p>
          </div>

          {/* Websites */}
          <div className="contact-box">
            <div className="contact-icon-box">
              <span className="material-icons contact-big-icon">language</span>
            </div>
            <h3 className="contact-title">Useful Websites</h3>
            <p><a href="https://msme.gov.in" target="_blank">msme.gov.in</a></p>
            <p><a href="https://udyamregistration.gov.in" target="_blank">Udyam Registration</a></p>
            <p><a href="https://champions.gov.in" target="_blank">MSME Champions Portal</a></p>
          </div>
        </div>

        {/* Social Media */}
        <div className="social-section">
          <h3 className="contact-title">Follow Us</h3>
          <div className="social-icons-row">
            <a href="https://twitter.com/msmeindia" target="_blank" className="social-pill twitter">
              <span className="material-icons">share</span> Twitter
            </a>
            <a href="https://www.facebook.com/msme.gov.in/" target="_blank" className="social-pill facebook">
              <span className="material-icons">thumb_up</span> Facebook
            </a>
            <a href="https://www.youtube.com/c/MSMEGov" target="_blank" className="social-pill youtube">
              <span className="material-icons">play_circle</span> YouTube
            </a>
          </div>
        </div>

      </div>
    </div>
  );
}

export default Contact;
