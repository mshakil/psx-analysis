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
          <div
            key={idx}
            className={`px-3 py-1.5 rounded-full text-xs font-medium border transition whitespace-nowrap ${getBadgeStyles(badge.sentiment)}`}
          >
            <span className="mr-1">{getArrowIcon(badge.sentiment)}</span>
            {badge.text}
          </div>
        ))}
      </div>
    </div>
  );
}
