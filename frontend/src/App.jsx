//src/App.jsx
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/shared/Layout';
import UploadandConversionPage from './pages/PDFUploadandConversion.jsx';
import CreateProjectPage from './pages/CreateProject.jsx';
import UploadTasksPage from './pages/UploadTasks.jsx';
import StartPrelabellingPage from './pages/StartPrelabelling.jsx';
import ReviewAIPage from './pages/ReviewAI.jsx';
import GetResultsPage from './pages/GetResults.jsx';
import EvaluateAIPage from './pages/EvaluateAI.jsx';
import EvaluationDriftPage from './pages/EvaluationDrift.jsx';
import FinetuneAIPage from './pages/FinetuneAI.jsx';
import AboutPage from './pages/AboutPage.jsx';
import { AppProvider } from "./context/AppContext";

export default function App() {

  return (
    <AppProvider> 
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<UploadandConversionPage />} />
          <Route path="/aboutpage" element={<AboutPage />} />
          <Route path="/project" element={<CreateProjectPage />} />
          <Route path="/tasks" element={<UploadTasksPage />} />
          <Route path="/prelabelling" element={<StartPrelabellingPage />} />
          <Route path="/review" element={<ReviewAIPage />} />
          <Route path="/results" element={<GetResultsPage/>} />
          <Route path="/evaluate" element={<EvaluateAIPage />} />
          <Route path="/evaluationdrift" element={<EvaluationDriftPage />} />
          <Route path="/finetune" element={<FinetuneAIPage />} />
        </Routes>
      </Layout>
    </Router>
    </AppProvider>  
  );
}