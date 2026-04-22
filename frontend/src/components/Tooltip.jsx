import { useState } from "react";

export default function Tooltip({ children, text }) {
  const [isVisible, setIsVisible] = useState(false);

  if (!text) return children;

  return (
    <div className="relative w-full">
      <div
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
      >
        {children}
      </div>

      {isVisible && (
        <div className="fixed bg-gray-800 text-gray-100 text-xs rounded-md px-3 py-2 border border-gray-600 pointer-events-none z-50 shadow-lg max-w-xs whitespace-normal"
          style={{
            top: "0",
            left: "0",
            transform: "translate(-9999px, -9999px)",
          }}
          onMouseEnter={() => setIsVisible(true)}
          onMouseLeave={() => setIsVisible(false)}
          ref={(el) => {
            if (el && isVisible) {
              const rect = el.parentElement.getBoundingClientRect();
              const tooltipRect = el.getBoundingClientRect();
              let top = rect.top - tooltipRect.height - 12;
              let left = rect.left + rect.width / 2 - tooltipRect.width / 2;

              // Check if tooltip goes off top of screen
              if (top < 0) {
                top = rect.bottom + 12;
              }

              // Check if tooltip goes off left side
              if (left < 0) {
                left = 10;
              }

              // Check if tooltip goes off right side
              if (left + tooltipRect.width > window.innerWidth) {
                left = window.innerWidth - tooltipRect.width - 10;
              }

              el.style.top = `${top + window.scrollY}px`;
              el.style.left = `${left}px`;
              el.style.transform = "none";
            }
          }}
        >
          {text}
        </div>
      )}
    </div>
  );
}
