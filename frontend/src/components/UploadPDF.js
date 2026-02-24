import React, { useState } from "react";
import { uploadPDF } from "../services/api";

function UploadPDF() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [records, setRecords] = useState(null);
  const [fileName, setFileName] = useState("");

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setFileName(selectedFile.name);
      setStatus("");
      setRecords(null);
    }
  };

  const handleReset = () => {
    setFile(null);
    setFileName("");
    setStatus("");
    setRecords(null);
    // Reset file input
    document.getElementById("pdf-upload").value = "";
  };

  const handleUpload = async () => {
    if (!file) {
      setStatus("Please select a PDF file to upload.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    setRecords(null);
    setStatus("Processing intelligence report...");

    try {
      const res = await uploadPDF(formData);

      if (res.data.status === "success") {
        setStatus("File processed successfully!");
        setRecords(`${res.data.records} records extracted. Excel file saved as: ${res.data.excel}`);
      } else {
        setStatus(res.data.message || "Error processing PDF.");
      }
    } catch (err) {
      console.error("Upload error:", err);

      if (err.response) {
        setStatus(err.response.data.message || "Server error occurred.");
      } else {
        setStatus("Network error. Please check backend connection.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-form-container">
      <div className="form-paper">
        <div className="form-section">
          <h2 className="form-title">Upload Intelligence PDF</h2>
          <p className="form-description">
            Upload a PDF document containing intelligence data to extract structured operational information.
            The system will automatically process tables and narrative content.
          </p>
        </div>

        {/* Alert Messages */}
        {status && (
          <div
            className={`alert ${
              loading
                ? "alert-info"
                : records
                ? "alert-success"
                : "alert-error"
            }`}
          >
            <span className="alert-icon">
              {loading ? "⏳" : records ? "✅" : "⚠️"}
            </span>
            <span className="alert-message">{status}</span>
          </div>
        )}

        {records && (
          <div className="alert alert-success">
            <span className="alert-icon">📄</span>
            <span className="alert-message">{records}</span>
          </div>
        )}

        {/* Form Fields */}
        <div className="form-group">
          <label htmlFor="pdf-upload" className="form-label">
            Select PDF File <span className="required">*</span>
          </label>
          <div className="file-input-wrapper">
            <input
              id="pdf-upload"
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              disabled={loading}
              className="file-input"
            />
            {fileName && (
              <div className="file-name-display">
                <span className="file-icon">📄</span>
                <span className="file-name">{fileName}</span>
              </div>
            )}
          </div>
          <p className="form-helper-text">
            Upload intelligence PDF reports (structured tables or narrative format)
          </p>
        </div>

        {/* Action Buttons */}
        <div className="form-actions">
          <button
            onClick={handleUpload}
            disabled={loading || !file}
            className="btn btn-primary"
          >
            {loading ? (
              <>
                <span className="spinner-small"></span>
                Processing...
              </>
            ) : (
              <>📤 Upload & Extract</>
            )}
          </button>

          <button
            onClick={handleReset}
            disabled={loading}
            className="btn btn-secondary"
          >
            🔄 Reset
          </button>
        </div>

        {/* Loading Indicator */}
        {loading && (
          <div className="loading-container">
            <div className="spinner"></div>
            <p className="loading-text">
              Extracting data from PDF... This may take a moment.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default UploadPDF;