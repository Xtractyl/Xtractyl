export default function ReviewAICard() {
    const LS_BASE = import.meta.env.VITE_LS_BASE || "http://localhost:8080";
    const PROJECT_ID = 1; // später gern dynamisch/aus Zustand
  
    return (
    <div className="p-8 bg-xtractyl-background min-h-screen text-xtractyl-darktext">
        <h1 className="text-2xl font-semibold mb-4">Review AI</h1>
        <p className=" text-xtractyl-outline/70 mb-4">
          Check and correct the AI-generated results using Label Studio.
        </p>
  
        <a
          href={`${LS_BASE}/projects/`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block bg-xtractyl-orange text-xtractyl-white text-xtractyl-outline/70ase font-medium px-5 py-2 rounded shadow hover:bg-xtractyl-orange-600 transition"
        >
          Open in Label Studio
        </a>
  
        <p className="mt-3 text-sm  text-xtractyl-outline/60">
          Return to this tab after review.
        </p>
      </div>
    );
  }