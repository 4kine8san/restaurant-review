interface Props {
  value: number | null;
}

export default function StarDisplay({ value }: Props) {
  if (!value) return <span className="text-gray-400">-</span>;
  return (
    <span className="text-amber-500">
      {"★".repeat(value)}
      {"☆".repeat(5 - value)}
    </span>
  );
}
