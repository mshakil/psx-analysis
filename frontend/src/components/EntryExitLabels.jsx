import Tooltip from "./Tooltip";

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
          <Tooltip text="The price at which the stock is trading right now. This is what you would pay if you buy today.">
            <div className="bg-gray-800/50 rounded p-3 border border-gray-700 cursor-help">
              <p className="text-xs text-gray-500">Current Price</p>
              <p className="text-lg font-bold text-white">
                PKR {currentPrice ? currentPrice.toFixed(2) : "—"}
              </p>
            </div>
          </Tooltip>

          {/* Entry Range */}
          <Tooltip text="The best price range to buy this stock. Wait for the price to drop into this zone before buying. It's like waiting for a sale before purchasing.">
            <div className="bg-gray-800/50 rounded p-3 border border-gray-700 cursor-help">
              <p className="text-xs text-gray-500 mb-1">{entryExit.entry_label}</p>
              <p className="text-xs text-emerald-400 font-semibold">
                PKR {entryExit.entry_low.toFixed(2)} — {entryExit.entry_high.toFixed(2)}
              </p>
            </div>
          </Tooltip>

          {/* Stop Loss */}
          <Tooltip text="Your safety net. If the stock price drops below this level, it means your analysis was wrong. Sell immediately to prevent bigger losses. It protects you from losing too much money.">
            <div className="bg-gray-800/50 rounded p-3 border border-red-700/30 cursor-help">
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
          </Tooltip>
        </div>

        {/* Right column: Target Prices */}
        <div className="space-y-3">
          {/* Target 1 */}
          <Tooltip text="The first price level where you might want to sell part of your shares to lock in some profit. Think of it as a small win along the way.">
            <div className="bg-gray-800/50 rounded p-3 border border-blue-700/30 cursor-help">
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
          </Tooltip>

          {/* Target 2 */}
          <Tooltip text="The higher price target where you could sell the rest of your shares for maximum profit. This is the ambitious goal for this stock.">
            <div className="bg-gray-800/50 rounded p-3 border border-cyan-700/30 cursor-help">
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
          </Tooltip>

          {/* Risk/Reward Ratio */}
          <Tooltip text="For every PKR you risk losing, how much profit could you make? A ratio of 1:2.5 means if you lose 100 PKR, you could profit 250 PKR. Higher is better.">
            <div className={`rounded p-3 border border-gray-700 cursor-help ${getRRBgColor(entryExit.risk_reward_ratio)}`}>
              <p className="text-xs text-gray-500 mb-1">Risk/Reward Ratio</p>
              <p className={`text-sm font-bold ${getRRColor(entryExit.risk_reward_ratio)}`}>
                1:{entryExit.risk_reward_ratio.toFixed(2)}
              </p>
            </div>
          </Tooltip>
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
