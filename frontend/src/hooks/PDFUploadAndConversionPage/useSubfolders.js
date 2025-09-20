import { useState, useEffect, useCallback } from "react";
import { listSubfolders } from "../../api/PDFUploadAndConversionPage/api";

export default function useSubfolders() {
  const [existingFolders, setExistingFolders] = useState([]);
  const [loadingFolders, setLoading] = useState(false);
  const [foldersError, setError] = useState(null);

  const refreshSubfolders = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listSubfolders();
      setExistingFolders(Array.isArray(data) ? data : []);
      setError(null);
    } catch (e) {
      setExistingFolders([]);
      setError(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshSubfolders();
  }, [refreshSubfolders]);

  return { existingFolders, loadingFolders, foldersError, refreshSubfolders };
}