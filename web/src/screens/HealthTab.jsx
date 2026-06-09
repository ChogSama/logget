import React from "react";
import { format } from "date-fns";
import { motion } from "framer-motion";
import DailyScore from "@/components/logget/DailyScore";
import GoalTracker from "@/components/logget/GoalTracker";
import DailyReview from "@/components/logget/DailyReview";
import AiCheckin from "@/components/logget/AiCheckin";
import ScreenTimeTracker from "@/components/logget/ScreenTimeTracker";

export default function HealthTab({ selectedDate, healthData }) {
  const dateStr = format(selectedDate, "EEEE, MMM d");

  return (
    <div className="pb-4">
      {/* Header */}
      <div className="px-6 pt-10 pb-2">
        <p className="text-xs font-black uppercase tracking-widest text-neutral-400">your daily vibe</p>
        <motion.p
          key={dateStr}
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-sm font-semibold text-neutral-400 mt-1"
        >
          {dateStr}
        </motion.p>
      </div>

      <motion.div
        key={format(selectedDate, "yyyy-MM-dd")}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="px-5 space-y-6 pb-4"
      >
        <DailyScore score={healthData?.score} subtitle={healthData?.subtitle} />
        <GoalTracker
          goalName={healthData?.goal_name}
          progress={healthData?.goal_progress}
          dailyNote={healthData?.goal_daily_note}
        />
        <DailyReview pros={healthData?.pros} cons={healthData?.cons} />
        <AiCheckin messages={healthData?.ai_messages} />
        <ScreenTimeTracker hours={healthData?.screen_time_hours} />
      </motion.div>
    </div>
  );
}