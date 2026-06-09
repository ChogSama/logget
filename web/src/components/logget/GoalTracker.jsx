import React from "react";
import { motion } from "framer-motion";
import { Target } from "lucide-react";

export default function GoalTracker({ goalName, progress, dailyNote }) {
  const name = goalName || "6-Pack in 3 Months";
  const pct = progress || 34;
  const note = dailyNote || "Today's routine added +2% to your goal. Keep it up!";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="border border-border rounded-3xl p-6"
    >
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-2xl bg-secondary flex items-center justify-center">
          <Target className="w-5 h-5" />
        </div>
        <div>
          <h3 className="font-black font-display text-base">Target</h3>
          <p className="text-sm font-semibold text-muted-foreground">{name}</p>
        </div>
      </div>

      {/* Progress bar */}
      <div className="relative h-4 bg-secondary rounded-full overflow-hidden mb-3">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 1, ease: "easeOut", delay: 0.4 }}
          className="absolute left-0 top-0 h-full bg-foreground rounded-full"
        />
      </div>

      <div className="flex items-center justify-between mb-3">
        <span className="text-2xl font-black font-display">{pct}%</span>
        <span className="text-xs font-bold text-muted-foreground bg-secondary px-3 py-1 rounded-full">
          Goal Active
        </span>
      </div>

      <p className="text-sm font-semibold text-muted-foreground leading-relaxed">
        {note}
      </p>
    </motion.div>
  );
}