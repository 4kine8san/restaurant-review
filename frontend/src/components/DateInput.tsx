import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

interface Props {
  value: string;
  onChange: (value: string) => void;
  className?: string;
}

const WEEKDAYS = ["日", "月", "火", "水", "木", "金", "土"];

function parseYearMonth(v: string): { year: number; month: number } {
  const parts = v.replace(/-/g, "/").split("/");
  const year = parseInt(parts[0]);
  const month = parseInt(parts[1]);
  const now = new Date();
  return {
    year: isNaN(year) ? now.getFullYear() : year,
    month: isNaN(month) ? now.getMonth() + 1 : month,
  };
}

function normalizeDate(raw: string): string {
  const digits = raw.replace(/\D/g, "");
  if (digits.length === 8) {
    return `${digits.slice(0, 4)}/${digits.slice(4, 6)}/${digits.slice(6, 8)}`;
  }
  if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) {
    return raw.replace(/-/g, "/");
  }
  return raw;
}

export default function DateInput({ value, onChange, className }: Props) {
  const [open, setOpen] = useState(false);
  const [calYear, setCalYear] = useState(() => parseYearMonth(value).year);
  const [calMonth, setCalMonth] = useState(() => parseYearMonth(value).month);
  const [popupStyle, setPopupStyle] = useState<React.CSSProperties>({});
  const anchorRef = useRef<HTMLDivElement>(null);
  const popupRef = useRef<HTMLDivElement>(null);

  // カレンダーの表示位置をアンカー要素に合わせて計算
  const updatePopupPosition = () => {
    if (!anchorRef.current) return;
    const rect = anchorRef.current.getBoundingClientRect();
    const spaceBelow = window.innerHeight - rect.bottom;
    const popupHeight = 280;
    const top =
      spaceBelow >= popupHeight
        ? rect.bottom + window.scrollY + 4
        : rect.top + window.scrollY - popupHeight - 4;
    setPopupStyle({
      position: "absolute",
      top,
      left: rect.left + window.scrollX,
      width: 256,
    });
  };

  useEffect(() => {
    if (!open) {
      const { year, month } = parseYearMonth(value);
      setCalYear(year);
      setCalMonth(month);
    }
  }, [value, open]);

  useEffect(() => {
    if (!open) return;
    updatePopupPosition();

    const handler = (e: MouseEvent) => {
      if (
        anchorRef.current?.contains(e.target as Node) ||
        popupRef.current?.contains(e.target as Node)
      )
        return;
      setOpen(false);
    };
    const onScroll = () => updatePopupPosition();
    document.addEventListener("mousedown", handler);
    window.addEventListener("scroll", onScroll, true);
    return () => {
      document.removeEventListener("mousedown", handler);
      window.removeEventListener("scroll", onScroll, true);
    };
  }, [open]);

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    const formatted = normalizeDate(e.target.value);
    if (formatted !== e.target.value) onChange(formatted);
  };

  const openCalendar = () => {
    const { year, month } = parseYearMonth(value);
    setCalYear(year);
    setCalMonth(month);
    setOpen((prev) => !prev);
  };

  const prevMonth = () => {
    if (calMonth === 1) { setCalMonth(12); setCalYear((y) => y - 1); }
    else setCalMonth((m) => m - 1);
  };

  const nextMonth = () => {
    if (calMonth === 12) { setCalMonth(1); setCalYear((y) => y + 1); }
    else setCalMonth((m) => m + 1);
  };

  const selectDay = (day: number) => {
    const m = String(calMonth).padStart(2, "0");
    const d = String(day).padStart(2, "0");
    onChange(`${calYear}/${m}/${d}`);
    setOpen(false);
  };

  const selectToday = () => {
    const now = new Date();
    const m = String(now.getMonth() + 1).padStart(2, "0");
    const d = String(now.getDate()).padStart(2, "0");
    onChange(`${now.getFullYear()}/${m}/${d}`);
    setOpen(false);
  };

  const daysInMonth = new Date(calYear, calMonth, 0).getDate();
  const firstDayOfWeek = new Date(calYear, calMonth - 1, 1).getDay();
  const [selYear, selMonth, selDay] = value.split("/").map(Number);
  const today = new Date();

  const calendar = (
    <div
      ref={popupRef}
      style={{ ...popupStyle, zIndex: 9999 }}
      className="bg-white border border-gray-200 rounded-xl shadow-lg p-3"
    >
      <div className="flex items-center justify-between mb-3">
        <button
          type="button"
          onClick={prevMonth}
          className="w-7 h-7 flex items-center justify-center rounded hover:bg-gray-100 text-gray-600 text-xs"
        >
          ◀
        </button>
        <span className="text-sm font-semibold text-gray-700">
          {calYear}年 {calMonth}月
        </span>
        <button
          type="button"
          onClick={nextMonth}
          className="w-7 h-7 flex items-center justify-center rounded hover:bg-gray-100 text-gray-600 text-xs"
        >
          ▶
        </button>
      </div>

      <div className="grid grid-cols-7 text-center mb-1">
        {WEEKDAYS.map((d, i) => (
          <span
            key={d}
            className={`text-xs font-medium pb-1 ${
              i === 0 ? "text-red-400" : i === 6 ? "text-blue-400" : "text-gray-400"
            }`}
          >
            {d}
          </span>
        ))}
      </div>

      <div className="grid grid-cols-7 text-center gap-y-0.5">
        {Array.from({ length: firstDayOfWeek }, (_, i) => (
          <span key={`e${i}`} />
        ))}
        {Array.from({ length: daysInMonth }, (_, i) => {
          const day = i + 1;
          const col = (firstDayOfWeek + i) % 7;
          const isSelected =
            selYear === calYear && selMonth === calMonth && selDay === day;
          const isToday =
            today.getFullYear() === calYear &&
            today.getMonth() + 1 === calMonth &&
            today.getDate() === day;
          return (
            <button
              key={day}
              type="button"
              onClick={() => selectDay(day)}
              className={[
                "w-8 h-8 mx-auto rounded-full text-sm leading-none transition-colors",
                isSelected ? "bg-amber-600 text-white font-bold" : "hover:bg-amber-100",
                isToday && !isSelected ? "ring-1 ring-amber-400 font-semibold" : "",
                !isSelected && col === 0 ? "text-red-500" : "",
                !isSelected && col === 6 ? "text-blue-500" : "",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              {day}
            </button>
          );
        })}
      </div>

      <div className="mt-2 pt-2 border-t border-gray-100 text-center">
        <button
          type="button"
          onClick={selectToday}
          className="text-xs text-amber-600 hover:text-amber-800 hover:underline"
        >
          今日
        </button>
      </div>
    </div>
  );

  return (
    <div ref={anchorRef} className="relative">
      <div className="flex gap-1">
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onBlur={handleBlur}
          placeholder="例: 2026/04/19"
          maxLength={10}
          className={className}
        />
        <button
          type="button"
          onClick={openCalendar}
          className="px-2.5 border border-gray-300 rounded-lg text-gray-500 hover:bg-amber-50 hover:border-amber-400 text-sm"
          title="カレンダーで選択"
        >
          📅
        </button>
      </div>

      {open && createPortal(calendar, document.body)}
    </div>
  );
}
