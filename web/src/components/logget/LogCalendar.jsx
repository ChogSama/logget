import React from "react";
import { motion } from "framer-motion";
import { ChevronLeft, ChevronRight, Play } from "lucide-react";
import { format, startOfMonth, endOfMonth, startOfWeek, endOfWeek, addDays, isSameMonth, isSameDay, addMonths, subMonths } from "date-fns";

export default function LogCalendar({ currentMonth, setCurrentMonth, selectedDate, onSelectDate, daysWithVlogs }) {
  const monthStart = startOfMonth(currentMonth);
  const monthEnd = endOfMonth(monthStart);
  const calStart = startOfWeek(monthStart);
  const calEnd = endOfWeek(monthEnd);

  const days = [];
  let day = calStart;
  while (day <= calEnd) {
    days.push(day);
    day = addDays(day, 1);
  }

  const weekdays = ["S", "M", "T", "W", "T", "F", "S"];

  const hasVlog = (d) => {
    const dateStr = format(d, "yyyy-MM-dd");
    return daysWithVlogs.includes(dateStr);
  };

  return (
    <div className="px-1">
      {/* Month navigation */}
      <div className="flex items-center justify-between mb-6">
        <motion.button
          whileTap={{ scale: 0.9 }}
          onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}
          className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center"
        >
          <ChevronLeft className="w-5 h-5" />
        </motion.button>
        <h2 className="text-xl font-black font-display">
          {format(currentMonth, "MMMM yyyy")}
        </h2>
        <motion.button
          whileTap={{ scale: 0.9 }}
          onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}
          className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center"
        >
          <ChevronRight className="w-5 h-5" />
        </motion.button>
      </div>

      {/* Weekday headers */}
      <div className="grid grid-cols-7 mb-2">
        {weekdays.map((wd, i) => (
          <div key={i} className="text-center text-xs font-bold text-muted-foreground py-2">
            {wd}
          </div>
        ))}
      </div>

      {/* Day grid */}
      <div className="grid grid-cols-7 gap-y-1">
        {days.map((d, i) => {
          const isCurrentMonth = isSameMonth(d, monthStart);
          const isSelected = isSameDay(d, selectedDate);
          const isToday = isSameDay(d, new Date());
          const hasVideo = hasVlog(d);

          return (
            <motion.button
              key={i}
              whileTap={{ scale: 0.88 }}
              onClick={() => isCurrentMonth && onSelectDate(d)}
              className={`relative flex flex-col items-center justify-center h-12 rounded-2xl transition-all duration-200 ${
                !isCurrentMonth
                  ? "opacity-20 pointer-events-none"
                  : isSelected
                  ? "bg-foreground"
                  : isToday
                  ? "bg-secondary"
                  : "hover:bg-secondary/50"
              }`}
            >
              <span
                className={`text-sm font-extrabold font-display leading-none ${
                  isSelected ? "text-background" : "text-foreground"
                }`}
              >
                {format(d, "d")}
              </span>
              {hasVideo && (
                <Play
                  className={`w-2.5 h-2.5 mt-0.5 ${
                    isSelected ? "text-background/60" : "text-foreground/30"
                  }`}
                  fill="currentColor"
                />
              )}
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}