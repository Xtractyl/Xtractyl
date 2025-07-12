// src/pages/Home.jsx
import PDFManager from '../components/PDFManager';
console.log('Home-Komponente wird gerendert');
export default function Home() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">PDF-Upload</h1>
      <PDFManager />
    </div>
  );
}