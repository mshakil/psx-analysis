import { useState } from "react";
import SearchBar from "./components/SearchBar";
import AnalysisCard from "./components/AnalysisCard";
import PriceChart from "./components/PriceChart";
import LoadingState from "./components/LoadingState";
import ErrorBanner from "./components/ErrorBanner";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export default function App() {
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [checklist, setChecklist] = useState(null);

  const handleAnalyze = async (inputTicker) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setTicker(inputTicker);

    try {
      const resp = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker: inputTicker, checklist }),
      });

      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.detail || "Analysis failed");
      }

      const data = await resp.json();
      setResult(data);
      setChecklist(data.checklist);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 font-sans">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4 flex items-center gap-3">
        <div className="text-2xl font-bold text-emerald-400">Intelli-Trade</div>
        <span className="text-xs bg-emerald-900 text-emerald-300 px-2 py-0.5 rounded-full">
          PSX AI
        </span>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8 space-y-6">
        <SearchBar onAnalyze={handleAnalyze} loading={loading} />

        {loading && <LoadingState ticker={ticker} />}
        {error && <ErrorBanner message={error} />}

        {result && (
          <>
            <AnalysisCard result={result} />
            {result.recent_prices && (
              <PriceChart data={result.recent_prices} ticker={result.ticker} />
            )}
          </>
        )}
      </main>
    </div>
  );
}
