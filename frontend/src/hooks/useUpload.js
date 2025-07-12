// src/hooks/useUpload.js
import { useState } from 'react';

export default function useUpload() {
  const [uploadStatus, setUploadStatus] = useState([]);

  const uploadPDFs = async (files) => {
    const formData = new FormData();
    for (const file of files) {
      formData.append('pdfs', file);
    }

    try {
      const response = await fetch('/api/convert', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      setUploadStatus(data.status || ['Upload abgeschlossen']);
    } catch (error) {
      console.error('Fehler beim Upload:', error);
      setUploadStatus(['Fehler beim Upload']);
    }
  };

  return { uploadPDFs, uploadStatus };
}