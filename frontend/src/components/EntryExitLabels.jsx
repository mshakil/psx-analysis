const TileCard = ({ label, value, tooltip, subtext, borderColor = "border-gray-700", textColor = "text-white" }) => {
  return (
    <div className={`group relative bg-gray-800/50 rounded-lg p-4 border ${borderColor} cursor-help h-full transition-all hover:bg-gray-800`}>
      <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">{label}</p>
      <p className={`text-lg font-bold ${textColor}`}>{value}</p>
      {subtext && <p className="text-xs text-gray-400 mt-2">{subtext}</p>}

      {/* Tooltip */}
      {tooltip && (
        <div className="absolute left-1/2 bottom-full transform -translate-x-1/2 mb-3 px-3 py-2 bg-gray-800 text-gray-100 text-xs rounded-md border border-gray-600 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-40 pointer-events-auto whitespace-normal w-max max-w-xs shadow-xl">
          {tooltip}
          {/* Arrow */}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-800" />
        </div>
      )}
    </div>
  );
};

export default function EntryExitLabels({ entryExit, currentPrice }) {
  if (!entryExit) {
    return null;
  }

  const getRRColor = (ratio) => {
    if (ratio >= 2.5) return "text-emerald-400";
    if (ratio >= 1.5) return "text-yellow-400";
    return "text-red-400";
  };

  const getRRBgColor = (ratio) => {
    if (ratio >= 2.5) return "bg-emerald-900/20 border-emerald-700/30";
    if (ratio >= 1.5) return "bg-yellow-900/20 border-yellow-700/30";
    return "bg-red-900/20 border-red-700/30";
  };

  return (
    <div className="bg-gray-900 rounded-lg p-6 border border-gray-700">
      <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-6">Entry & Exit Levels</h3>

      {/* 2x3 Grid Layout */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {/* Left Column */}
        <TileCard
          label="Current Price"
          value={`PKR ${currentPrice ? currentPrice.toFixed(2) : "—"}`}
          tooltip="The price at which the stock is trading right now. This is what you would pay if you buy today."
        />

        <TileCard
          label={entryExit.entry_label}
          value={`PKR ${entryExit.entry_low.toFixed(2)} — ${entryExit.entry_high.toFixed(2)}`}
          textColor="text-emerald-400"
          borderColor="border-emerald-700/30"
          tooltip="The best price range to buy this stock. Wait for the price to drop into this zone before buying. It's like waiting for a sale before purchasing."
        />

        <TileCard
          label="Protective Stop"
          value={`PKR ${entryExit.stop_loss.toFixed(2)}`}
          textColor="text-red-400"
          borderColor="border-red-700/30"
          subtext={currentPrice && entryExit.stop_loss > 0 ? `Risk: PKR ${(currentPrice - entryExit.stop_loss).toFixed(2)}` : null}
          tooltip="Your safety net. If the stock price drops below this level, sell immediately to prevent bigger losses. It protects you from losing too much money."
        />

        {/* Right Column */}
        <TileCard
          label={entryExit.target1_label}
          value={`PKR ${entryExit.target1.toFixed(2)}`}
          textColor="text-blue-400"
          borderColor="border-blue-700/30"
          subtext={currentPrice && entryExit.target1 > currentPrice ? `Upside: ${((entryExit.target1 - currentPrice) / currentPrice * 100).toFixed(1)}%` : null}
          tooltip="The first price level where you might want to sell part of your shares to lock in some profit. Think of it as a small win along the way."
        />

        <TileCard
          label={entryExit.target2_label}
          value={`PKR ${entryExit.target2.toFixed(2)}`}
          textColor="text-cyan-400"
          borderColor="border-cyan-700/30"
          subtext={currentPrice && entryExit.target2 > currentPrice ? `Upside: ${((entryExit.target2 - currentPrice) / currentPrice * 100).toFixed(1)}%` : null}
          tooltip="The higher price target where you could sell the rest of your shares for maximum profit. This is the ambitious goal for this stock."
        />

        <TileCard
          label="Risk/Reward Ratio"
          value={`1:${entryExit.risk_reward_ratio.toFixed(2)}`}
          textColor={getRRColor(entryExit.risk_reward_ratio)}
          borderColor={getRRBgColor(entryExit.risk_reward_ratio)}
          tooltip="For every PKR you risk losing, how much profit could you make? A ratio of 1:2.5 means if you lose 100 PKR, you could profit 250 PKR. Higher is better."
        />
      </div>

      {/* Disclaimer */}
      <div className="bg-gray-800/30 rounded-lg p-3 border border-gray-700 border-dashed">
        <p className="text-xs text-gray-500 italic">
          ⚠️ Not financial advice. For educational purposes only. Always do your own research.
        </p>
      </div>
    </div>
  );
}
