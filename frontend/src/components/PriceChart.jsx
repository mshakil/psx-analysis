import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function PriceChart({ data, ticker }) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 text-center text-gray-500">
        No price data available
      </div>
    );
  }

  const minPrice = Math.min(...data.map((d) => d.close));
  const maxPrice = Math.max(...data.map((d) => d.close));
  const padding = (maxPrice - minPrice) * 0.1;

  const isUptrend = data[data.length - 1].close > data[0].close;

  return (
    <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
      <h3 className="text-sm text-gray-500 uppercase tracking-wider font-semibold mb-4">
        30-Day Price History
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
              <stop
                offset="5%"
                stopColor={isUptrend ? "#10b981" : "#ef4444"}
                stopOpacity={0.3}
              />
              <stop
                offset="95%"
                stopColor={isUptrend ? "#10b981" : "#ef4444"}
                stopOpacity={0}
              />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="date" stroke="#6b7280" style={{ fontSize: "12px" }} />
          <YAxis
            stroke="#6b7280"
            style={{ fontSize: "12px" }}
            domain={[
              minPrice - padding,
              maxPrice + padding,
            ]}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1f2937",
              border: "1px solid #374151",
              borderRadius: "8px",
            }}
            formatter={(value, name) => {
              if (name === "close") {
                return [`PKR ${value.toFixed(2)}`, "Close Price"];
              }
              if (name === "volume") {
                return [
                  `${(value / 1000000).toFixed(2)}M`,
                  "Volume",
                ];
              }
              return [value, name];
            }}
          />
          <Area
            type="monotone"
            dataKey="close"
            stroke={isUptrend ? "#10b981" : "#ef4444"}
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorPrice)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
