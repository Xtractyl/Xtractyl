import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import UploadandConversionPage from './pages/PDFUploadandConversion.jsx';
import CreateProjectPage from './pages/CreateProject.jsx';
import UploadTasksPage from './pages/UploadTasks.jsx';
import StartPrelabellingPage from './pages/StartPrelabelling.jsx';
import ReviewAIPage from './pages/ReviewAI.jsx';
import GetResultsPage from './pages/GetResults.jsx';
import EvaluateAIPage from './pages/EvaluateAI.jsx';
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
          <Route path="/prelabelling" element={<StartPrelabellingPage />} />
          <Route path="/review" element={<ReviewAIPage />} />
          <Route path="/results" element={<GetResultsPage />} />
          <Route path="/evaluate" element={<EvaluateAIPage />} />
        </Routes>
      </Layout>
    </Router>
  );
}