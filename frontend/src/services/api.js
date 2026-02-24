import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:5000",
});

export const uploadPDF = (formData) =>
  API.post("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export const exportToExcel = async (data, filename = "intelligence_data") => {
  try {
    const response = await API.post("/export", 
      { data, filename },
      { responseType: "blob" }
    );
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    
    // Extract filename from Content-Disposition header if available
    const contentDisposition = response.headers["content-disposition"];
    let downloadFilename = `${filename}_export.xlsx`;
    
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i);
      if (filenameMatch && filenameMatch[1]) {
        downloadFilename = filenameMatch[1];
      }
    }
    
    link.setAttribute("download", downloadFilename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
    
    return response;
  } catch (error) {
    console.error("Export error:", error);
    throw error;
  }
};
