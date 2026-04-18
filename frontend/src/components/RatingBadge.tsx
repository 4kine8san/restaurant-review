interface Props {
  value: number | null;
  label?: string;
}

function color(v: number): string {
  if (v >= 4.0) return "bg-green-100 text-green-800";
  if (v >= 3.0) return "bg-blue-100 text-blue-800";
  if (v >= 2.0) return "bg-yellow-100 text-yellow-800";
  return "bg-red-100 text-red-800";
}

export default function RatingBadge({ value, label }: Props) {
  if (!value) return null;
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${color(value)}`}
    >
      {label && <span className="opacity-70">{label}</span>}
      {value.toFixed(1)}
    </span>
  );
}
