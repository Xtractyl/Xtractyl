// frontend/src/components/EvaluationDriftPage/EvaluationDriftCard.jsx
import EvaluationDriftView from "./EvaluationDriftView";

export default function EvaluationDriftCard() {
  return (
    <div className="p-8 bg-xtractyl-background min-h-screen text-xtractyl-darktext">
      <h1 className="text-2xl font-semibold mb-4">Evaluation Drift</h1>
      <p className="text-xtractyl-outline/70">
        This feature is currently worked on. It will display evaluation drift for a standard dataset over time.
      </p>

      <EvaluationDriftView />
    </div>
  );
}