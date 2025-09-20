// src/hooks/PDFUploadAndConversionPage/useFilesInFolder.js
import { useState, useEffect, useCallback, useRef } from "react";
import { listFiles } from "../../api/PDFUploadAndConversionPage/api";

/**
 * @param {string} folder - aktueller Foldername
 * @param {string[]} existingFolders - Liste gültiger Ordner
 * @param {number} debounceMs - Verzögerung bevor gefetcht wird
 */
export default function useFilesInFolder(folder, existingFolders = [], debounceMs = 300) {
  const [filesInSelectedFolder, setFiles] = useState([]);
  const [loadingFiles, setLoading] = useState(false);
  const [filesError, setError] = useState(null);
  const timerRef = useRef(null);

  const refreshFilesInFolder = useCallback(
    async (f = folder) => {
      if (!f) {
        setFiles([]);
        return;
      }
      // nur fetchen, wenn Ordner *wirklich* existiert
      if (!existingFolders.includes(f)) {
        setFiles([]);
        setError(null);
        return;
      }

      setLoading(true);
      try {
        const data = await listFiles(f);
        setFiles(Array.isArray(data) ? data : []);
        setError(null);
      } catch (e) {
        // 404 vom Server => als "leer" behandeln statt Fehler zu zeigen
        if (e?.status === 404) {
          setFiles([]);
          setError(null);
        } else {
          setFiles([]);
          setError(e);
        }
      } finally {
        setLoading(false);
      }
    },
    [folder, existingFolders]
  );

  useEffect(() => {
    // Debounce: erst fetchen, wenn kurze Tipp-Pause war
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => refreshFilesInFolder(folder), debounceMs);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [folder, refreshFilesInFolder, debounceMs]);

  return { filesInSelectedFolder, loadingFiles, filesError, refreshFilesInFolder };
}