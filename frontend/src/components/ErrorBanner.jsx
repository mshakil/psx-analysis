import { useState } from "react";

export default function ErrorBanner({ message }) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <div className="bg-red-900 border border-red-700 rounded-xl p-4 flex items-start gap-3">
      <span className="text-red-400 font-bold mt-0.5">!</span>
      <div className="flex-1">
        <h3 className="text-red-300 font-semibold">Analysis Failed</h3>
        <p className="text-red-200 text-sm mt-1">{message}</p>
        <p className="text-red-300 text-xs mt-2">
          💡 Tip: Check the ticker symbol (e.g., HBL, ENGRO) and try again.
        </p>
      </div>
      <button
        onClick={() => setDismissed(true)}
        className="text-red-400 hover:text-red-300 font-bold"
      >
        ✕
      </button>
    </div>
  );
}
