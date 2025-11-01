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
    const savedToken = localStorage.getItem("apiToken");
    if (savedToken) setApiToken(savedToken);
  }, []);

  const handleTokenSave = (token) => {
    setApiToken(token);
    localStorage.setItem("apiToken", token);
  };

  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<UploadandConversionPage />} />
          <Route path="/project" element={<CreateProjectPage onTokenSave={handleTokenSave} />} />
          <Route path="/tasks" element={<UploadTasksPage apiToken={apiToken} />} />
          <Route path="/prelabelling" element={<StartPrelabellingPage apiToken={apiToken}  />} />
          <Route path="/review" element={<ReviewAIPage />} />
          <Route path="/results" element={<GetResultsPage apiToken={apiToken}  />} />
          <Route path="/evaluate" element={<EvaluateAIPage />} />
          <Route path="/finetune" element={<FinetuneAIPage />} />
         <Route path="/library" element={<PDFLibraryPage/>} />
         <Route path="/question" element={<AskQuestionPage/>} />
         <Route path="/uploadanswer" element={<ReviewandUploadAnswerPage/>} />
        </Routes>
      </Layout>
    </Router>
  );
}