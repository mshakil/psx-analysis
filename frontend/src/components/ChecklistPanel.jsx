const STATUS_STYLES = {
  DONE: "text-emerald-400",
  FAILED: "text-red-400",
  PENDING: "text-gray-500",
};

const STATUS_ICONS = {
  DONE: "✓",
  FAILED: "✗",
  PENDING: "◯",
};

export default function ChecklistPanel({ checklist }) {
  if (!checklist || Object.keys(checklist).length === 0) return null;

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
        Analysis Checklist
      </h3>
      <ul className="space-y-1.5">
        {Object.entries(checklist).map(([task, status]) => (
          <li key={task} className="flex items-center gap-2 text-sm">
            <span className={STATUS_STYLES[status] || "text-gray-500"}>
              {STATUS_ICONS[status] || "?"}
            </span>
            <span className="text-gray-300 capitalize">
              {task.replace(/_/g, " ")}
            </span>
            <span className={`ml-auto text-xs font-mono ${STATUS_STYLES[status]}`}>
              {status}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
