import React from "react";
import { motion } from "framer-motion";

export default function DailyReview({ pros, cons }) {
  const displayPros = pros?.length > 0 ? pros : [
    "Got 8 hours of sleep",
    "Finished the React assignment",
  ];
  const displayCons = cons?.length > 0 ? cons : [
    "Skipped lunch at 1:00 PM",
    "Doom-scrolled TikTok for 2h",
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
    >
      <h3 className="text-lg font-black font-display mb-4">Daily Review</h3>
      <div className="grid grid-cols-2 gap-3">
        {/* Pros */}
        <div className="border border-border rounded-3xl p-5">
          <p className="text-sm font-black font-display mb-4">✨ Pros</p>
          <div className="space-y-3">
            {displayPros.map((pro, i) => (
              <p key={i} className="text-xs font-semibold text-muted-foreground leading-relaxed">
                {pro}
              </p>
            ))}
          </div>
        </div>

        {/* Cons */}
        <div className="border border-border rounded-3xl p-5">
          <p className="text-sm font-black font-display mb-4">⚠️ Cons</p>
          <div className="space-y-3">
            {displayCons.map((con, i) => (
              <p key={i} className="text-xs font-semibold text-muted-foreground leading-relaxed">
                {con}
              </p>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}