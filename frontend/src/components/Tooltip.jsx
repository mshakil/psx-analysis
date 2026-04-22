export default function Tooltip({ children, text }) {
  if (!text) return children;

  return (
    <div className="group relative inline-block w-full">
      {children}

      {/* Tooltip - appears on hover */}
      <div className="absolute left-1/2 bottom-full transform -translate-x-1/2 mb-3 px-3 py-2 bg-gray-800 text-gray-100 text-xs rounded-md border border-gray-600 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-40 pointer-events-auto whitespace-normal w-max max-w-xs shadow-xl">
        {text}
        {/* Tooltip arrow */}
        <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-800" />
      </div>
    </div>
  );
}
