import React from "react";
import "./App.css";
import UploadPDF from "./components/UploadPDF";

function App() {
  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="logo-section">
            <img src="/logo192.png" alt="Logo" className="app-logo" />
            <h1 className="app-title">Intelligence Data Extraction System</h1>
          </div>
          <p className="app-subtitle">Automated PDF Intelligence Processing</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="app-main">
        <div className="content-wrapper">
          <UploadPDF />
        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <div className="footer-content">
          <div className="footer-info">
            <p className="footer-text">
              Developed by Apt Software Avenues Pvt. Ltd.
            </p>
            <p className="footer-subtext">
              A Defender Framework Tool | Hybrid Rule-Based Architecture
            </p>
          </div>
          <div className="footer-copyright">
            <p>© {new Date().getFullYear()} Intelligence Data Extraction Engine. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
