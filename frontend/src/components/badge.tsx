interface BadgeProps {
  label: string;
  variant?: "default" | "success" | "warning" | "danger" | "info";
}

const variants = {
  default: "bg-gray-500/10 text-gray-400 border border-gray-500/20",
  success: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20",
  warning: "bg-amber-500/10 text-amber-400 border border-amber-500/20",
  danger: "bg-rose-500/10 text-rose-400 border border-rose-500/20",
  info: "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20",
};

export function Badge({ label, variant = "default" }: BadgeProps) {
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium ${variants[variant]}`}>
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
