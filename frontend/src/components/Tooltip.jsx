import { useState } from "react";

export default function Tooltip({ children, text }) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div className="relative inline-block group">
      {children}
      {text && (
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-800 text-gray-200 text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-normal max-w-xs border border-gray-600 pointer-events-none z-10">
          {text}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-800" />
        </div>
      )}
    </div>
  );
}
