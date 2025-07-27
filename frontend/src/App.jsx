import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import UploadandConversionPage from './pages/PDFUploadandConversion.jsx';
import CreateProjectPage from './pages/CreateProject.jsx';
import StartPrelabellingPage from './pages/StartPrelabelling.jsx';
import ReviewAIPage from './pages/ReviewAI.jsx';
import GetResultsPage from './pages/GetResults.jsx';
import EvaluateAIPage from './pages/EvaluateAI.jsx';
import { useState } from 'react';

export default function App() {
  const [apiToken, setApiToken] = useState("");

  return (
<Router>
  <Layout>
    <Routes>
      <Route path="/" element={<UploadandConversionPage />} />
      <Route path="/project" element={<CreateProjectPage />} />
      <Route path="/prelabelling" element={<StartPrelabellingPage />} />
      <Route path="/review" element={<ReviewAIPage />} />
      <Route path="/results" element={<GetResultsPage />} />
      <Route path="/evaluate" element={<EvaluateAIPage />} />
    </Routes>
  </Layout>
</Router>
  );
}