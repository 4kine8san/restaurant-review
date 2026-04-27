import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import client from "../api/client";

type XAxisKey = "genre" | "scene" | "stars" | "visit_year" | "visit_month" | "prefecture";
type YAxisKey = "count" | "rating_avg";

interface StatPoint {
  label: string;
  value: number;
}

interface StatsResponse {
  x_axis: XAxisKey;
  y_axis: YAxisKey;
  data: StatPoint[];
}

const X_OPTIONS: { value: XAxisKey; label: string }[] = [
  { value: "genre", label: "ジャンル" },
  { value: "scene", label: "利用シーン" },
  { value: "stars", label: "星" },
  { value: "visit_year", label: "訪問年" },
  { value: "visit_month", label: "訪問月" },
  { value: "prefecture", label: "都道府県" },
];

const Y_OPTIONS: { value: YAxisKey; label: string }[] = [
  { value: "count", label: "レビュー数" },
  { value: "rating_avg", label: "平均評価" },
];

export default function ChartPage() {
  const [xAxis, setXAxis] = useState<XAxisKey>("genre");
  const [yAxis, setYAxis] = useState<YAxisKey>("count");
  const [data, setData] = useState<StatPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    client
      .get<StatsResponse>(`/stats/?x_axis=${xAxis}&y_axis=${yAxis}`)
      .then((res) => setData(res.data.data))
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [xAxis, yAxis]);

  const yLabel = Y_OPTIONS.find((o) => o.value === yAxis)?.label ?? "";
  const xLabel = X_OPTIONS.find((o) => o.value === xAxis)?.label ?? "";

  return (
    <div className="min-h-screen">
      <header className="bg-white/80 backdrop-blur-sm shadow-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center gap-4">
          <Link to="/" className="text-amber-600 hover:text-amber-800">
            ← 一覧
          </Link>
          <h1 className="text-lg font-bold text-amber-800">グラフ</h1>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-6">
        <div className="bg-white/80 rounded-xl shadow-sm p-4 mb-6 flex flex-wrap gap-6 items-center">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-600 w-10">X 軸</span>
            <div className="flex rounded-lg border border-gray-300 overflow-hidden">
              {X_OPTIONS.map((o) => (
                <button
                  key={o.value}
                  type="button"
                  onClick={() => setXAxis(o.value)}
                  className={`px-3 py-1.5 text-sm transition-colors ${
                    xAxis === o.value
                      ? "bg-amber-600 text-white"
                      : "hover:bg-gray-100"
                  }`}
                >
                  {o.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-600 w-10">Y 軸</span>
            <div className="flex rounded-lg border border-gray-300 overflow-hidden">
              {Y_OPTIONS.map((o) => (
                <button
                  key={o.value}
                  type="button"
                  onClick={() => setYAxis(o.value)}
                  className={`px-3 py-1.5 text-sm transition-colors ${
                    yAxis === o.value
                      ? "bg-amber-600 text-white"
                      : "hover:bg-gray-100"
                  }`}
                >
                  {o.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="bg-white/80 rounded-xl shadow-sm p-6">
          <p className="text-sm text-gray-500 mb-6">
            {xLabel}別 {yLabel}
          </p>

          {error && (
            <div className="p-3 mb-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          {loading ? (
            <div className="flex justify-center py-24 text-gray-400 text-sm">
              読み込み中...
            </div>
          ) : data.length === 0 ? (
            <div className="flex justify-center py-24 text-gray-400 text-sm">
              データがありません
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={420}>
              <BarChart
                data={data}
                margin={{ top: 5, right: 20, left: 10, bottom: 70 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="label"
                  angle={-40}
                  textAnchor="end"
                  interval={0}
                  tick={{ fontSize: 12, fill: "#6b7280" }}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: "#6b7280" }}
                  allowDecimals={yAxis !== "count"}
                />
                <Tooltip
                  formatter={(v) => [
                    typeof v === "number"
                      ? yAxis === "count"
                        ? v
                        : v.toFixed(2)
                      : v,
                    yLabel,
                  ]}
                  contentStyle={{
                    borderRadius: "8px",
                    border: "1px solid #e5e7eb",
                    fontSize: "13px",
                  }}
                />
                <Bar dataKey="value" fill="#d97706" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </main>
    </div>
  );
}