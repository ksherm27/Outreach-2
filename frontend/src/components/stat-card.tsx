interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  color?: "blue" | "green" | "yellow" | "red" | "purple" | "gray";
}

const colorMap = {
  blue: {
    border: "border-cyan-500/20",
    value: "text-cyan-400",
    glow: "hover:border-cyan-500/40 hover:shadow-[0_0_15px_rgba(6,182,212,0.05)]",
  },
  green: {
    border: "border-emerald-500/20",
    value: "text-emerald-400",
    glow: "hover:border-emerald-500/40 hover:shadow-[0_0_15px_rgba(16,185,129,0.05)]",
  },
  yellow: {
    border: "border-amber-500/20",
    value: "text-amber-400",
    glow: "hover:border-amber-500/40 hover:shadow-[0_0_15px_rgba(245,158,11,0.05)]",
  },
  red: {
    border: "border-rose-500/20",
    value: "text-rose-400",
    glow: "hover:border-rose-500/40 hover:shadow-[0_0_15px_rgba(244,63,94,0.05)]",
  },
  purple: {
    border: "border-violet-500/20",
    value: "text-violet-400",
    glow: "hover:border-violet-500/40 hover:shadow-[0_0_15px_rgba(139,92,246,0.05)]",
  },
  gray: {
    border: "border-[#2a2a3a]",
    value: "text-gray-300",
    glow: "hover:border-gray-500/40",
  },
};

export function StatCard({ title, value, subtitle, color = "blue" }: StatCardProps) {
  const c = colorMap[color];
  return (
    <div
      className={`rounded-xl border bg-[#111118] p-5 transition-all duration-200 ${c.border} ${c.glow}`}
    >
      <p className="text-[11px] font-medium uppercase tracking-wider text-gray-500">{title}</p>
      <p className={`mt-2 text-3xl font-bold ${c.value}`}>{value}</p>
      {subtitle && <p className="mt-1 text-xs text-gray-500">{subtitle}</p>}
    </div>
  );
}
