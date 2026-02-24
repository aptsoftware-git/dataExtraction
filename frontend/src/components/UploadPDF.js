import React, { useState } from "react";
import { uploadPDF } from "../services/api";

function UploadPDF() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [records, setRecords] = useState(null);

  const handleUpload = async () => {
    if (!file) {
      setStatus("❌ Please select a PDF file.");
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
        setStatus("✅ File processed successfully.");
        setRecords(`📁 Saved as: ${res.data.excel}`);
      } else {
        setStatus(`❌ ${res.data.message || "Error processing PDF."}`);
      }
    } catch (err) {
      console.error("Upload error:", err);

      if (err.response) {
        setStatus(`❌ ${err.response.data.message || "Server error occurred."}`);
      } else {
        setStatus("❌ Network error. Check backend connection.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="card">
        <h2>Automated Intelligence Extraction System</h2>
        <p>
          Upload an intelligence PDF to extract structured operational data.
        </p>

        <div className="upload-zone">
          <strong>Select Intelligence PDF</strong>
          <br />
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => setFile(e.target.files[0])}
            disabled={loading}
          />
        </div>

        <button onClick={handleUpload} disabled={loading}>
          {loading ? "Processing..." : "Upload & Extract"}
        </button>

        {loading && <div className="spinner"></div>}

        {status && (
          <div
            className={`status ${
              loading
                ? "processing"
                : status.startsWith("✅")
                ? "success"
                : "error"
            }`}
          >
            {status}
          </div>
        )}

        {records && (
          <div className="status success">
            {records}
          </div>
        )}
      </div>
    </div>
  );
}

export default UploadPDF;