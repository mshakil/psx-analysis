import { useEffect, useRef, useState } from "react";
import { createChart } from "lightweight-charts";

export default function CandlestickChart({ ohlcv, sma20, sma60, ticker, signalsLoading }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const [timeframe, setTimeframe] = useState(30);
  const [isResizing, setIsResizing] = useState(false);

  useEffect(() => {
    if (!containerRef.current || !ohlcv || ohlcv.length === 0) return;

    // Create chart
    const chart = createChart(containerRef.current, {
      layout: {
        textColor: "#d1d5db",
        background: { color: "#111827" },
      },
      grid: {
        vertLines: { color: "#374151" },
        hLines: { color: "#374151" },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
      width: containerRef.current.clientWidth,
      height: 500,
    });

    chartRef.current = chart;

    // Slice data to timeframe
    let slicedOhlcv = ohlcv;
    if (ohlcv.length > timeframe) {
      slicedOhlcv = ohlcv.slice(-timeframe);
    }

    // Candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor: "#10b981",
      downColor: "#ef4444",
      wickUpColor: "#10b981",
      wickDownColor: "#ef4444",
      borderUpColor: "#059669",
      borderDownColor: "#dc2626",
    });

    // Convert data to chart format (time as unix timestamp)
    const candleData = slicedOhlcv.map((bar) => ({
      time: Math.floor(new Date(bar.date).getTime() / 1000),
      open: bar.open,
      high: bar.high,
      low: bar.low,
      close: bar.close,
    }));

    candleSeries.setData(candleData);

    // Volume histogram series
    const volumeSeries = chart.addHistogramSeries({
      color: "#6b7280",
      priceFormat: { type: "volume" },
    });

    const volumeData = slicedOhlcv.map((bar) => ({
      time: Math.floor(new Date(bar.date).getTime() / 1000),
      value: bar.volume,
      color: bar.close >= bar.open ? "#10b98144" : "#ef444444",
    }));

    volumeSeries.setData(volumeData);

    // SMA20 line series
    if (sma20) {
      const sma20Series = chart.addLineSeries({
        color: "#f59e0b",
        lineWidth: 2,
        title: "SMA20",
      });

      const sma20Data = slicedOhlcv.map((bar) => ({
        time: Math.floor(new Date(bar.date).getTime() / 1000),
        value: sma20,
      }));

      sma20Series.setData(sma20Data);
    }

    // SMA60 line series
    if (sma60) {
      const sma60Series = chart.addLineSeries({
        color: "#8b5cf6",
        lineWidth: 2,
        title: "SMA60",
      });

      const sma60Data = slicedOhlcv.map((bar) => ({
        time: Math.floor(new Date(bar.date).getTime() / 1000),
        value: sma60,
      }));

      sma60Series.setData(sma60Data);
    }

    // Fit content
    chart.timeScale().fitContent();

    // ResizeObserver for responsive design
    const resizeObserver = new ResizeObserver(() => {
      if (!isResizing && containerRef.current) {
        setIsResizing(true);
        setTimeout(() => {
          if (containerRef.current) {
            chart.applyOptions({
              width: containerRef.current.clientWidth,
            });
            setIsResizing(false);
          }
        }, 300);
      }
    });

    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    // Cleanup
    return () => {
      resizeObserver.disconnect();
      chart.remove();
    };
  }, [ohlcv, sma20, sma60, timeframe, isResizing]);

  if (!ohlcv || ohlcv.length === 0) {
    return (
      <div className="bg-gray-900 rounded-lg p-6 border border-gray-700">
        <p className="text-gray-400">Loading chart data...</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
      {/* Timeframe tabs */}
      <div className="flex gap-2 mb-4">
        {[30, 60, 90, 252].map((tf) => (
          <button
            key={tf}
            onClick={() => setTimeframe(tf)}
            className={`px-3 py-1 rounded text-sm font-medium transition ${
              timeframe === tf
                ? "bg-emerald-600 text-white"
                : "bg-gray-800 text-gray-400 hover:bg-gray-700"
            }`}
          >
            {tf === 252 ? "1Y" : `${tf}D`}
          </button>
        ))}
      </div>

      {/* Chart container */}
      <div
        ref={containerRef}
        style={{ width: "100%", height: 500 }}
        className="rounded"
      />

      {/* Legend */}
      <div className="flex gap-4 mt-4 text-xs text-gray-400">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-emerald-500 rounded-full" />
          <span>Up</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-red-500 rounded-full" />
          <span>Down</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 border-2 border-amber-500 rounded-full" />
          <span>SMA20</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 border-2 border-purple-500 rounded-full" />
          <span>SMA60</span>
        </div>
      </div>
    </div>
  );
}
