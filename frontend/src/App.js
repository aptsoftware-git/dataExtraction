import React from "react";
import "./App.css";
import UploadPDF from "./components/UploadPDF";
import docIntelLogo from "./assets/DocIntel.png";
import makeInIndiaLogo from "./assets/Make_In_India.png";

function App() {
  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="logo-section">
            <img src={docIntelLogo} alt="Intelligence Data Extraction Logo" className="app-logo" />
            <h1 className="app-title">Intelligence Data Extraction System</h1>
          </div>
          <p className="app-subtitle">Automated PDF Intelligence Processing</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="app-main">
        <UploadPDF />
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <div className="footer-content">
          <div className="footer-top">
            <div className="footer-logo">
              <img src={makeInIndiaLogo} alt="Make In India" className="make-in-india-logo" />
            </div>
            <div className="footer-info">
              <p className="footer-text">
                Developed by Apt Software Avenues Pvt. Ltd.
              </p>
              <p className="footer-subtext">
                A Defender Framework Tool | Hybrid Rule-Based Architecture
              </p>
            </div>
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
