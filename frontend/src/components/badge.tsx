interface BadgeProps {
  label: string;
  variant?: "default" | "success" | "warning" | "danger" | "info";
}

const variants = {
  default: "bg-gray-100 text-gray-700",
  success: "bg-green-100 text-green-700",
  warning: "bg-yellow-100 text-yellow-700",
  danger: "bg-red-100 text-red-700",
  info: "bg-blue-100 text-blue-700",
};

export function Badge({ label, variant = "default" }: BadgeProps) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${variants[variant]}`}>
      {label}
    </span>
  );
}

export function replyTypeBadgeVariant(type: string | null): BadgeProps["variant"] {
  switch (type) {
    case "positive": return "success";
    case "objection": return "warning";
    case "unsubscribe": return "danger";
    case "ooo_with_date":
    case "ooo_no_date": return "info";
    default: return "default";
  }
}

export function statusBadgeVariant(status: string | null): BadgeProps["variant"] {
  switch (status) {
    case "launched": return "success";
    case "paused": return "warning";
    case "completed": return "info";
    case "failed": return "danger";
    default: return "default";
  }
}
