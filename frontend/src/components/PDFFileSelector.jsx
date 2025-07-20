import React from "react";

export default function PDFFileSelector({ files, setFiles, folder, setFolder }) {
  const handleFileChange = (e) => {
    setFiles([...e.target.files]);
  };

  const handleFolderChange = (e) => {
    setFolder(e.target.value.trim());
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block font-medium">Your subfolder (e.g. "oncology-july")</label>
        <input
          type="text"
          value={folder}
          onChange={handleFolderChange}
          placeholder="Unterordner eingeben"
          required
          className="w-full p-2 border rounded"
        />
      </div>

      <div>
        <label className="block font-medium">PDF-Dateien auswählen</label>
        <input
          type="file"
          accept="application/pdf"
          multiple
          onChange={handleFileChange}
          required
          className="w-full p-2 border rounded"
        />
        {files.length > 0 && (
          <p className="mt-2 text-sm text-gray-600">
            {files.length} Datei(en) ausgewählt
          </p>
        )}
      </div>
    </div>
  );
}