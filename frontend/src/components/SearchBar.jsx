import { useState } from "react";

export default function SearchBar({ onAnalyze, loading }) {
  const [input, setInput] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim()) {
      onAnalyze(input.toUpperCase().trim());
      setInput("");
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-gray-900 rounded-xl p-6 border border-gray-800 space-y-4"
    >
      <div className="flex flex-col gap-2">
        <label className="text-sm font-semibold text-gray-300">
          Enter PSX Ticker
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value.toUpperCase())}
            placeholder="e.g., HBL, ENGRO, LUCK"
            disabled={loading}
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-emerald-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-700 disabled:cursor-not-allowed px-6 py-2 rounded-lg font-semibold text-white transition"
          >
            {loading ? "Analyzing..." : "Analyze"}
          </button>
        </div>
      </div>
      <p className="text-xs text-gray-500">
        Popular: <span className="font-mono">HBL • ENGRO • LUCK • TRG • MCB</span>
      </p>
    </form>
  );
}
