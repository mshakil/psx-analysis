export default function EntryExitLabels({ entryExit, currentPrice }) {
  if (!entryExit) {
    return null;
  }

  // Determine risk/reward color
  const getRRColor = (ratio) => {
    if (ratio >= 2.5) return "text-emerald-400";
    if (ratio >= 1.5) return "text-yellow-400";
    return "text-red-400";
  };

  const getRRBgColor = (ratio) => {
    if (ratio >= 2.5) return "bg-emerald-900/20";
    if (ratio >= 1.5) return "bg-yellow-900/20";
    return "bg-red-900/20";
  };

  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-700 space-y-4">
      <h3 className="text-sm font-semibold text-gray-300">Entry & Exit Levels</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Left column: Entry & Stop Loss */}
        <div className="space-y-3">
          {/* Current Price */}
          <div className="bg-gray-800/50 rounded p-3 border border-gray-700">
            <p className="text-xs text-gray-500">Current Price</p>
            <p className="text-lg font-bold text-white">
              PKR {currentPrice ? currentPrice.toFixed(2) : "—"}
            </p>
          </div>

          {/* Entry Range */}
          <div className="bg-gray-800/50 rounded p-3 border border-gray-700">
            <p className="text-xs text-gray-500 mb-1">{entryExit.entry_label}</p>
            <p className="text-xs text-emerald-400 font-semibold">
              PKR {entryExit.entry_low.toFixed(2)} — {entryExit.entry_high.toFixed(2)}
            </p>
          </div>

          {/* Stop Loss */}
          <div className="bg-gray-800/50 rounded p-3 border border-red-700/30">
            <p className="text-xs text-gray-500 mb-1">{entryExit.stop_label}</p>
            <p className="text-xs text-red-400 font-semibold">
              PKR {entryExit.stop_loss.toFixed(2)}
            </p>
            {currentPrice && entryExit.stop_loss > 0 && (
              <p className="text-xs text-gray-500 mt-1">
                Risk: PKR {(currentPrice - entryExit.stop_loss).toFixed(2)}
              </p>
            )}
          </div>
        </div>

        {/* Right column: Target Prices */}
        <div className="space-y-3">
          {/* Target 1 */}
          <div className="bg-gray-800/50 rounded p-3 border border-blue-700/30">
            <p className="text-xs text-gray-500 mb-1">{entryExit.target1_label}</p>
            <p className="text-xs text-blue-400 font-semibold">
              PKR {entryExit.target1.toFixed(2)}
            </p>
            {currentPrice && entryExit.target1 > currentPrice && (
              <p className="text-xs text-gray-500 mt-1">
                Upside: {((entryExit.target1 - currentPrice) / currentPrice * 100).toFixed(1)}%
              </p>
            )}
          </div>

          {/* Target 2 */}
          <div className="bg-gray-800/50 rounded p-3 border border-cyan-700/30">
            <p className="text-xs text-gray-500 mb-1">{entryExit.target2_label}</p>
            <p className="text-xs text-cyan-400 font-semibold">
              PKR {entryExit.target2.toFixed(2)}
            </p>
            {currentPrice && entryExit.target2 > currentPrice && (
              <p className="text-xs text-gray-500 mt-1">
                Upside: {((entryExit.target2 - currentPrice) / currentPrice * 100).toFixed(1)}%
              </p>
            )}
          </div>

          {/* Risk/Reward Ratio */}
          <div className={`rounded p-3 border border-gray-700 ${getRRBgColor(entryExit.risk_reward_ratio)}`}>
            <p className="text-xs text-gray-500 mb-1">Risk/Reward Ratio</p>
            <p className={`text-sm font-bold ${getRRColor(entryExit.risk_reward_ratio)}`}>
              1:{entryExit.risk_reward_ratio.toFixed(2)}
            </p>
          </div>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="bg-gray-800/30 rounded p-3 border border-gray-700 border-dashed">
        <p className="text-xs text-gray-500 italic">
          ⚠️ Not financial advice. For educational purposes only. Always do your own research.
        </p>
      </div>
    </div>
  );
}
