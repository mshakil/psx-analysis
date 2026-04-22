import { useState, useEffect } from "react";

const MESSAGES = [
  "Fetching market data...",
  "Analyzing news...",
  "Running AI analysis...",
  "Validating output...",
];

export default function LoadingState({ ticker }) {
  const [messageIndex, setMessageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((i) => (i + 1) % MESSAGES.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-gray-900 rounded-xl p-8 border border-gray-800 text-center space-y-4">
      <div className="inline-block">
        <div className="flex gap-2 justify-center">
          <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce"></div>
          <div
            className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce"
            style={{ animationDelay: "0.1s" }}
          ></div>
          <div
            className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce"
            style={{ animationDelay: "0.2s" }}
          ></div>
        </div>
      </div>
      <div>
        <p className="text-gray-400 font-semibold">
          Analyzing {ticker}
        </p>
        <p className="text-sm text-gray-500 mt-2 h-5">
          {MESSAGES[messageIndex]}
        </p>
      </div>
    </div>
  );
}
