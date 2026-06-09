import React from "react";
import { motion } from "framer-motion";
import { Smartphone } from "lucide-react";

export default function ScreenTimeTracker({ hours }) {
  const displayHours = hours ?? 2.5;
  const maxHours = 6;
  const pct = Math.min((displayHours / maxHours) * 100, 100);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
      className="border border-border rounded-3xl p-6"
    >
      <div className="flex items-center gap-2 mb-1">
        <Smartphone className="w-5 h-5" />
        <span className="text-base font-black font-display">Doom-scrolling Reality Check 🛑</span>
      </div>

      <p className="text-sm font-semibold text-muted-foreground mb-5">
        {displayHours} hours scrolling today.
      </p>

      <div className="flex items-baseline gap-1 mb-4">
        <span className="text-5xl font-black font-display">{displayHours}</span>
        <span className="text-base font-bold text-muted-foreground">/ {maxHours}h limit</span>
      </div>

      <div className="relative h-4 bg-secondary rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 1, ease: "easeOut", delay: 0.6 }}
          className={`absolute left-0 top-0 h-full rounded-full ${
            displayHours > 4 ? "bg-destructive" : "bg-foreground"
          }`}
        />
      </div>

      <p className="text-xs font-semibold text-muted-foreground mt-3">
        {displayHours > 4
          ? "Whoa, that's a lot. Consider a screen detox 🧘"
          : displayHours > 2
          ? "Getting up there — maybe take a walk? 🚶"
          : "Great balance today! 👏"}
      </p>
    </motion.div>
  );
}