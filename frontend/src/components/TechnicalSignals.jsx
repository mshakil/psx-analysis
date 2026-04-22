import Tooltip from "./Tooltip";

const signalTooltips = {
  "Clear upward trend": "The stock price is consistently going up. This is a positive sign.",
  "Downward pressure on price": "The stock price is consistently going down. Be cautious.",
  "Strong buying momentum": "Many people are buying this stock right now. Energy is positive.",
  "Moderate buying pressure": "Some people are buying, but not overwhelming. Mixed energy.",
  "Weak momentum — cautious": "Few people are buying. The energy is low and uncertain.",
  "Buyers losing interest": "People who were buying are now selling. Momentum is fading.",
  "Heavy trading interest today": "Many shares are being traded today. There's active interest in this stock.",
  "Low trader participation": "Very few shares are being traded. Not many people are interested.",
  "Wide price swings — higher risk": "The price jumps around a lot. It's less predictable and riskier.",
  "Calm price movement": "The price is steady and stable. It doesn't jump around much.",
  "Price near support zone": "The price is at a level where it has bounced up before. It might go up from here.",
  "Price approaching resistance": "The price is at a level where it has been blocked before. It might fall back here.",
  "No clear direction": "The stock doesn't have a clear trend. It's moving sideways.",
};

export default function TechnicalSignals({ badges, loading }) {
  // Sort badges by category priority
  const categoryOrder = ["trend", "momentum", "volume", "volatility", "support_resistance"];
  const sortedBadges = badges
    ? [...badges].sort(
        (a, b) => categoryOrder.indexOf(a.category) - categoryOrder.indexOf(b.category)
      )
    : [];

  const getBadgeStyles = (sentiment) => {
    switch (sentiment) {
      case "BULLISH":
        return "bg-emerald-900 text-emerald-300 border-emerald-700";
      case "BEARISH":
        return "bg-red-900 text-red-300 border-red-700";
      case "NEUTRAL":
        return "bg-yellow-900 text-yellow-300 border-yellow-700";
      default:
        return "bg-gray-800 text-gray-300 border-gray-700";
    }
  };

  const getArrowIcon = (sentiment) => {
    switch (sentiment) {
      case "BULLISH":
        return "↑";
      case "BEARISH":
        return "↓";
      case "NEUTRAL":
        return "→";
      default:
        return "•";
    }
  };

  if (loading) {
    return (
      <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Technical Signals</h3>
        <div className="flex gap-2 flex-wrap">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="h-8 w-40 bg-gray-800 rounded-full animate-pulse"
            />
          ))}
        </div>
      </div>
    );
  }

  if (!badges || badges.length === 0) {
    return (
      <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Technical Signals</h3>
        <p className="text-sm text-gray-500">No signals available</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
      <h3 className="text-sm font-semibold text-gray-300 mb-3">Technical Signals</h3>
      <div className="flex gap-2 flex-wrap">
        {sortedBadges.map((badge, idx) => (
          <Tooltip key={idx} text={signalTooltips[badge.text] || "This signal indicates market conditions."}>
            <div
              className={`px-3 py-1.5 rounded-full text-xs font-medium border transition whitespace-nowrap cursor-help ${getBadgeStyles(badge.sentiment)}`}
            >
              <span className="mr-1">{getArrowIcon(badge.sentiment)}</span>
              {badge.text}
            </div>
          </Tooltip>
        ))}
      </div>
    </div>
  );
}
