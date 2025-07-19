export default function ReviewAI() {
  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">Review AI</h1>
      <p className="text-gray-600 mb-6">
        Check and correct the AI-generated results using Label Studio.
      </p>

      <a
        href="http://localhost:8080/projects/1"
        target="_blank"
        rel="noopener noreferrer"
        className="inline-block bg-xtractyl-orange text-white text-lg font-medium px-6 py-3 rounded-lg shadow hover:bg-orange-600 transition"
      >
        Open in Label Studio
      </a>

      <p className="mt-4 text-sm text-gray-500">
        Return to this tab after review.
      </p>
    </div>
  )
}