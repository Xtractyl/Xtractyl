import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/shared/Layout';
import UploadandConversionPage from './pages/PDFUploadandConversion.jsx';
import CreateProjectPage from './pages/CreateProject.jsx';
import UploadTasksPage from './pages/UploadTasks.jsx';
import StartPrelabellingPage from './pages/StartPrelabelling.jsx';
import ReviewAIPage from './pages/ReviewAI.jsx';
import GetResultsPage from './pages/GetResults.jsx';
import EvaluateAIPage from './pages/EvaluateAI.jsx';
import FinetuneAIPage from './pages/FinetuneAI.jsx';
import PDFLibraryPage from './pages/PDFLibrary.jsx';
import AskQuestionPage from './pages/AskQuestion.jsx';
import ReviewandUploadAnswerPage from './pages/ReviewandUploadAnswer.jsx';

import { useState, useEffect } from 'react';

export default function App() {
  const [apiToken, setApiToken] = useState("");

  useEffect(() => {
    // 1) Initial aus localStorage laden
    const savedToken = localStorage.getItem("apiToken");
    if (savedToken) setApiToken(savedToken);

    // 2) Auf Änderungen in localStorage reagieren (auch aus anderen Tabs/Fenstern)
    const handleStorageChange = (event) => {
      if (event.key === "apiToken") {
        setApiToken(event.newValue || "");
      }
    };
    window.addEventListener("storage", handleStorageChange);

    // Cleanup
    return () => window.removeEventListener("storage", handleStorageChange);
  }, []);

  const handleTokenSave = (token) => {
    setApiToken(token);
    localStorage.setItem("apiToken", token);
  };

  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<UploadandConversionPage apiToken={apiToken} />} />
          <Route path="/project" element={<CreateProjectPage apiToken={apiToken} onTokenSave={handleTokenSave} />} />
          <Route path="/tasks" element={<UploadTasksPage apiToken={apiToken} />} />
          <Route path="/prelabelling" element={<StartPrelabellingPage apiToken={apiToken}  />} />
          <Route path="/review" element={<ReviewAIPage apiToken={apiToken} />} />
          <Route path="/results" element={<GetResultsPage apiToken={apiToken}  />} />
          <Route path="/evaluate" element={<EvaluateAIPage apiToken={apiToken} />} />
          <Route path="/finetune" element={<FinetuneAIPage apiToken={apiToken} />} />
          <Route path="/library" element={<PDFLibraryPage apiToken={apiToken} />} />
          <Route path="/question" element={<AskQuestionPage apiToken={apiToken} />} />
          <Route path="/uploadanswer" element={<ReviewandUploadAnswerPage apiToken={apiToken} />} />
        </Routes>
      </Layout>
    </Router>
  );
}