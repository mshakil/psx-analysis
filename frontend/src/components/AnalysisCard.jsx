import Tooltip from "./Tooltip";
import ChecklistPanel from "./ChecklistPanel";

const VERDICT_STYLES = {
  "BUY NOW": "bg-emerald-600 text-white",
  "BUY SLOWLY": "bg-lime-600 text-white",
  HOLD: "bg-amber-600 text-white",
  "STAY AWAY": "bg-orange-600 text-white",
  SELL: "bg-red-600 text-white",
};

const RISK_COLORS = {
  LOW: "text-emerald-400",
  MEDIUM: "text-amber-400",
  HIGH: "text-red-400",
};

const getVerdictTooltip = (verdict) => {
  const tooltips = {
    "BUY NOW": "Strong positive signals. Good time to buy this stock.",
    "BUY SLOWLY": "Decent opportunity, but buy gradually instead of all at once. DCA (Dollar Cost Averaging) recommended.",
    HOLD: "Neither good nor bad. Just keep what you have if you own it.",
    "STAY AWAY": "Too much risk or too many warning signs. Don't buy right now.",
    SELL: "Strong negative signals. Time to exit if you own it.",
  };
  return tooltips[verdict] || "AI analysis on whether to buy, hold, or sell this stock.";
};

export default function AnalysisCard({ result }) {
  const confidencePercentage = result.confidence_score;

  return (
    <div className="space-y-4">
      {/* Verdict + Confidence */}
      <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 space-y-4">
        <div className="flex items-center justify-between gap-6">
          <div>
            <h2 className="text-sm text-gray-500 uppercase tracking-wider font-semibold mb-2">
              Verdict
            </h2>
            <Tooltip text={getVerdictTooltip(result.verdict)}>
              <span
                className={`inline-block px-4 py-2 rounded-full font-bold text-lg cursor-help ${
                  VERDICT_STYLES[result.verdict] || "bg-gray-700"
                }`}
              >
                {result.verdict}
              </span>
            </Tooltip>
          </div>
          <Tooltip text="How sure we are about this verdict. Higher percentage = higher confidence in the analysis. This is based on data quality, risk level, and agreement between positive and negative signals.">
            <div className="flex flex-col items-center gap-2 cursor-help">
              <div className="relative w-24 h-24">
                <svg viewBox="0 0 100 100" className="w-24 h-24">
                  <circle
                    cx="50"
                    cy="50"
                    r="45"
                    fill="none"
                    stroke="#374151"
                    strokeWidth="8"
                  />
                  <circle
                    cx="50"
                    cy="50"
                    r="45"
                    fill="none"
                    stroke="#10b981"
                    strokeWidth="8"
                    strokeDasharray={`${(confidencePercentage / 100) * 283} 283`}
                    strokeLinecap="round"
                    transform="rotate(-90 50 50)"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-emerald-400">
                      {confidencePercentage}%
                    </div>
                    <div className="text-xs text-gray-500">Confidence</div>
                  </div>
                </div>
              </div>
            </div>
          </Tooltip>
        </div>

        {/* Risk + Liquidity */}
        <div className="flex gap-4 pt-4 border-t border-gray-800">
          <Tooltip text="How much money you could lose if the stock price drops. HIGH = bigger potential loss, LOW = smaller potential loss.">
            <div className="flex-1 cursor-help">
              <div className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">
                Risk Level
              </div>
              <div className={`font-semibold ${RISK_COLORS[result.risk_level]}`}>
                {result.risk_level}
              </div>
            </div>
          </Tooltip>
          <Tooltip text="How easy it is to buy or sell this stock. STRONG = easy to trade, WEAK = hard to find buyers or sellers.">
            <div className="flex-1 cursor-help">
              <div className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">
                Liquidity
              </div>
              <div className="font-semibold text-blue-400">
                {result.liquidity_status}
              </div>
            </div>
          </Tooltip>
          <Tooltip text="How much reliable information we have about this stock. HIGH = lots of good data, LOW = limited information.">
            <div className="flex-1 cursor-help">
              <div className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">
                Data Quality
              </div>
              <div className="font-semibold text-purple-400">
                {result.data_quality}
              </div>
            </div>
          </Tooltip>
        </div>
      </div>

      {/* Summary */}
      <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
        <h3 className="text-sm text-gray-500 uppercase tracking-wider font-semibold mb-3">
          Analysis Summary
        </h3>
        <p className="text-gray-300 leading-relaxed text-sm">
          {result.summary_plain_english}
        </p>
      </div>

      {/* Bull + Bear Cases */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
          <h3 className="text-sm text-emerald-400 uppercase tracking-wider font-semibold mb-3">
            Bull Case
          </h3>
          <ul className="space-y-2">
            {result.bull_case.map((item, i) => (
              <li key={i} className="flex gap-2 text-sm text-gray-300">
                <span className="text-emerald-400 font-bold">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
          <h3 className="text-sm text-red-400 uppercase tracking-wider font-semibold mb-3">
            Bear Case
          </h3>
          <ul className="space-y-2">
            {result.bear_case.map((item, i) => (
              <li key={i} className="flex gap-2 text-sm text-gray-300">
                <span className="text-red-400 font-bold">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Key Drivers */}
      <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
        <h3 className="text-sm text-gray-500 uppercase tracking-wider font-semibold mb-3">
          Key Drivers
        </h3>
        <div className="flex flex-wrap gap-2">
          {result.key_drivers.map((driver, i) => (
            <span
              key={i}
              className="bg-gray-800 text-blue-300 px-3 py-1.5 rounded-full text-sm"
            >
              {driver}
            </span>
          ))}
        </div>
      </div>

      {/* Checklist */}
      {result.checklist && <ChecklistPanel checklist={result.checklist} />}
    </div>
  );
}
