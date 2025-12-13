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
import AboutPage from './pages/AboutPage.jsx';


import { useState, useEffect } from 'react';

export default function App() {
  const [apiToken, setApiToken] = useState("");
  const [projectName, setProjectName] = useState("");

useEffect(() => {
  const savedToken = localStorage.getItem("apiToken");
  if (savedToken) setApiToken(savedToken);
}, []);

  const handleTokenSave = (token) => {
    setApiToken(token);
    localStorage.setItem("apiToken", token);
  };

useEffect(() => {
  const saved = localStorage.getItem("projectName");
  if (saved) setProjectName(saved);
}, []);

const handleProjectNameSave = (name) => {
  setProjectName(name);
  localStorage.setItem("projectName", name);
};

  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<UploadandConversionPage />} />
          <Route path="/aboutpage" element={<AboutPage />} />
          <Route path="/project" element={<CreateProjectPage apiToken={apiToken} onTokenSave={handleTokenSave} onProjectNameSave={handleProjectNameSave}  />} />
          <Route path="/tasks" element={<UploadTasksPage apiToken={apiToken} projectName={projectName}  />} />
          <Route path="/prelabelling" element={<StartPrelabellingPage apiToken={apiToken} projectName={projectName} />} />
          <Route path="/review" element={<ReviewAIPage />} />
          <Route path="/results" element={<GetResultsPage apiToken={apiToken} projectName={projectName}  />} />
          <Route path="/evaluate" element={<EvaluateAIPage apiToken={apiToken} projectName={projectName} />} />
          <Route path="/finetune" element={<FinetuneAIPage apiToken={apiToken} projectName={projectName} />} />
          <Route path="/library" element={<PDFLibraryPage apiToken={apiToken} projectName={projectName} />} />
          <Route path="/question" element={<AskQuestionPage apiToken={apiToken} projectName={projectName} />} />
          <Route path="/uploadanswer" element={<ReviewandUploadAnswerPage apiToken={apiToken} projectName={projectName} />} />
        </Routes>
      </Layout>
    </Router>
  );
}