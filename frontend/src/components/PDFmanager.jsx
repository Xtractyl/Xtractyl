// src/components/PDFManager.jsx
import React, { useState } from 'react';
import useUpload from '../hooks/useUpload';

export default function PDFManager() {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const { uploadPDFs, uploadStatus } = useUpload();

  const handleFileChange = (e) => {
    setSelectedFiles([...e.target.files]);
  };

  const handleUpload = () => {
    if (selectedFiles.length > 0) {
      uploadPDFs(selectedFiles);
    }
  };

  return (
    <div className="space-y-4">
      <input type="file" accept=".pdf" multiple onChange={handleFileChange} />
      <button
        onClick={handleUpload}
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
      >
        Hochladen & Konvertieren
      </button>

      <div className="text-sm text-gray-600">
        {uploadStatus.map((status, i) => (
          <p key={i}>{status}</p>
        ))}
      </div>
    </div>
  );
}