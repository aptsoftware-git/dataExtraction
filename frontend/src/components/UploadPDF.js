import React, { useState } from "react";
import { uploadPDF, exportToExcel } from "../services/api";
import DataTable from "./DataTable";

function UploadPDF() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [fileName, setFileName] = useState("");
  const [extractedData, setExtractedData] = useState(null);
  const [selectedRows, setSelectedRows] = useState([]);
  const [exporting, setExporting] = useState(false);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setFileName(selectedFile.name);
      setStatus("");
    }
  };

  const handleReset = () => {
    setFile(null);
    setFileName("");
    setStatus("");
    setExtractedData(null);
    setSelectedRows([]);
    // Reset file input
    document.getElementById("pdf-upload").value = "";
  };

  const handleToggleRow = (index) => {
    setSelectedRows(prev => 
      prev.includes(index) 
        ? prev.filter(i => i !== index)
        : [...prev, index]
    );
  };

  const handleToggleAll = (data) => {
    if (selectedRows.length === data.length) {
      setSelectedRows([]);
    } else {
      setSelectedRows(data.map((_, index) => index));
    }
  };

  const handleSelectAll = () => {
    if (extractedData) {
      setSelectedRows(extractedData.map((_, index) => index));
    }
  };

  const handleDeselectAll = () => {
    setSelectedRows([]);
  };

  const handleExport = async () => {
    if (!extractedData || extractedData.length === 0) {
      setStatus("No data to export.");
      return;
    }

    try {
      setExporting(true);
      
      // Get selected data or all data
      const dataToExport = selectedRows.length > 0
        ? selectedRows.map(index => extractedData[index])
        : extractedData;

      // Extract original filename without extension
      const baseFilename = fileName.replace(/\.[^/.]+$/, "") || "intelligence_data";
      
      await exportToExcel(dataToExport, baseFilename);
      
      // Clear selection after successful export
      setSelectedRows([]);
    } catch (err) {
      console.error("Export error:", err);
      setStatus(err.response?.data?.message || "Failed to export data. Please try again.");
    } finally {
      setExporting(false);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setStatus("Please select a PDF file to upload.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    setStatus("Processing intelligence report...");

    try {
      const res = await uploadPDF(formData);

      if (res.data.status === "success") {
        setStatus("");
        setExtractedData(res.data.data || []);
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
    <>
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
                  : "alert-error"
              }`}
            >
              <span className="alert-icon">
                {loading ? "⏳" : "⚠️"}
              </span>
              <span className="alert-message">{status}</span>
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

      {/* Data Table - Outside form container for full width */}
      {extractedData && Array.isArray(extractedData) && extractedData.length > 0 && (
        <DataTable 
          data={extractedData}
          selectedRows={selectedRows}
          onToggleRow={handleToggleRow}
          onToggleAll={handleToggleAll}
          onSelectAll={handleSelectAll}
          onDeselectAll={handleDeselectAll}
          onExport={handleExport}
          exporting={exporting}
        />
      )}
    </>
  );
}

export default UploadPDF;