export default function Tooltip({ children, text }) {
  if (!text) return children;

  return (
    <div className="relative inline-block group w-full">
      {children}
      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-3 px-3 py-2 bg-gray-750 text-gray-100 text-xs rounded-md opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-normal max-w-xs border border-gray-600 pointer-events-none z-50 shadow-lg">
        {text}
        <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-750" />
      </div>
    </div>
  );
}
