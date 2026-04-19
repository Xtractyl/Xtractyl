//src/components/UploadTasksPage/HTMLFolderSelect.jsx
import { useEffect, useState } from "react";
import { getHtmlSubfolders } from "../../api/UploadTasksPage/api.js"; 

export default function HtmlFolderSelect({ selected, onChange }) {
  const [folders, setFolders] = useState([]);



  useEffect(() => {
    getHtmlSubfolders()
      .then(setFolders)
      .catch(() => setFolders([]));
  }, []);

  return (
    <div>
      <label className="block font-medium mb-1">
        Select HTML (Folder content will be sent to Label Studio)
      </label>
      <select
        value={selected}
        onChange={(e) => onChange(e.target.value)}
        required
        className="w-full p-2 border rounded"
      >
        <option value="">-- Select Folder --</option>
      {folders.map((f, i) => {
        const isGt = f.startsWith("Evaluation_Sets_Do_Not_Delete/");
        const label = isGt
          ? `🔒 GT: ${f.split("/").pop()}`
          : f;
        return (
          <option key={i} value={f}>
            {label}
          </option>
        );
      })}
      </select>
    </div>
  );
}