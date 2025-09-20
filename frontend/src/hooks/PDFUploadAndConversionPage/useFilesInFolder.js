import { useState, useEffect, useCallback } from "react";
import { listFiles } from "../../api/PDFUploadAndConversionPage/api";

export default function useFilesInFolder(folder) {
  const [filesInSelectedFolder, setFiles] = useState([]);
  const [loadingFiles, setLoading] = useState(false);
  const [filesError, setError] = useState(null);

  const refreshFilesInFolder = useCallback(
    async (f = folder) => {
      if (!f) {
        setFiles([]);
        return;
      }
      setLoading(true);
      try {
        const data = await listFiles(f);
        setFiles(Array.isArray(data) ? data : []);
        setError(null);
      } catch (e) {
        setFiles([]);
        setError(e);
      } finally {
        setLoading(false);
      }
    },
    [folder]
  );

  useEffect(() => {
    refreshFilesInFolder(folder);
  }, [folder, refreshFilesInFolder]);

  return { filesInSelectedFolder, loadingFiles, filesError, refreshFilesInFolder };
}