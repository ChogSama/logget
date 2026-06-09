import React from "react";
import { motion } from "framer-motion";

export default function DailyScore({ score, subtitle }) {
  const displayScore = score ?? 7.5;
  const displaySubtitle = subtitle || "Chaotically productive, but we forgot to hydrate! 😅";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className="text-center py-8"
    >
      <p className="text-xs font-black uppercase tracking-widest text-muted-foreground mb-4">
        Daily Vibe Score
      </p>
      <div className="inline-flex items-baseline gap-2">
        <span className="text-[96px] font-black font-display tracking-tight leading-none">
          {displayScore.toFixed(1)}
        </span>
        <span className="text-4xl font-bold text-muted-foreground font-display pb-3">
          / 10
        </span>
      </div>
      <p className="text-base font-semibold text-muted-foreground mt-4 max-w-[260px] mx-auto leading-relaxed">
        {displaySubtitle}
      </p>
    </motion.div>
  );
}