import React from "react";
import { motion } from "framer-motion";
import { format } from "date-fns";
import { Video, Target, ChevronRight } from "lucide-react";

export default function HomeTab({ logs = [], overview, onOpenCamera }) {
  const todayStr = format(new Date(), "yyyy-MM-dd");
  const todayClips = (logs || []).filter((e) => e.date === todayStr);
  const totalClipsNeeded = 5;
  const clipsRemaining = Math.max(0, totalClipsNeeded - todayClips.length);

  const goals = [
    { name: "6-Pack abs", progress: overview?.goal_progress || 34 },
    { name: "Study 4h daily", progress: 58 },
  ];

  const hour = new Date().getHours();
  const greeting =
    hour < 12 ? "Good Morning" : hour < 18 ? "Good Afternoon" : "Good Evening";

  return (
    <div className="min-h-screen pb-32">
      {/* Header */}
      <div className="flex items-center justify-between px-6 pt-14 pb-8">
        <div>
          <p className="text-sm font-bold text-muted-foreground">{greeting},</p>
          <h1 className="text-3xl font-black font-display tracking-tight leading-tight">
            Linh! 👋
          </h1>
        </div>
        <div className="w-12 h-12 rounded-full bg-foreground flex items-center justify-center">
          <span className="text-background font-black text-lg">L</span>
        </div>
      </div>

      <div className="px-5 space-y-5">
        {/* Today's Vlog Status Card */}
        <motion.button
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          whileTap={{ scale: 0.97 }}
          onClick={onOpenCamera}
          className="w-full bg-foreground text-background rounded-3xl p-6 text-left relative overflow-hidden"
        >
          <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-10">
            <Video className="w-24 h-24" />
          </div>
          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-2 h-2 rounded-full bg-background/60 animate-pulse" />
              <span className="text-xs font-black uppercase tracking-widest text-background/60">
                Today's Vlog
              </span>
            </div>
            {todayClips.length === 0 ? (
              <>
                <p className="text-xl font-black font-display leading-tight">
                  Start your vlog for{" "}
                  {format(new Date(), "MMMM d")}! 🎬
                </p>
                <p className="text-sm font-semibold text-background/60 mt-1">
                  Tap to record your first clip
                </p>
              </>
            ) : (
              <>
                <p className="text-xl font-black font-display leading-tight">
                  Continue today's vlog! ✨
                </p>
                <p className="text-sm font-semibold text-background/60 mt-1">
                  {todayClips.length} clip{todayClips.length > 1 ? "s" : ""} recorded
                  {clipsRemaining > 0 && ` · ${clipsRemaining} more to go`}
                </p>
              </>
            )}
          </div>
          <div className="relative z-10 flex items-center gap-1 mt-4">
            <span className="text-sm font-black text-background/80">Record now</span>
            <ChevronRight className="w-4 h-4 text-background/80" />
          </div>
        </motion.button>

        {/* Goals Card */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.12 }}
          className="border border-border rounded-3xl p-6"
        >
          <div className="flex items-center gap-2 mb-5">
            <Target className="w-5 h-5" />
            <h2 className="text-base font-black font-display">Current Targets</h2>
          </div>

          <div className="space-y-5">
            {goals.map((goal, i) => (
              <div key={i}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-bold">{goal.name}</span>
                  <span className="text-sm font-black font-display">{goal.progress}%</span>
                </div>
                <div className="relative h-3 bg-secondary rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${goal.progress}%` }}
                    transition={{ duration: 1.2, ease: "easeOut", delay: 0.3 + i * 0.15 }}
                    className="absolute left-0 top-0 h-full bg-foreground rounded-full"
                  />
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Daily Score Preview */}
        {overview && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="border border-border rounded-3xl p-6 flex items-center justify-between"
          >
            <div>
              <p className="text-xs font-black uppercase tracking-widest text-muted-foreground mb-1">
                Today's Vibe Score
              </p>
              <p className="text-sm font-semibold text-muted-foreground leading-snug max-w-[220px]">
                {overview.subtitle}
              </p>
            </div>
            <div className="text-right shrink-0 ml-4">
              <span className="text-5xl font-black font-display leading-none">
                {overview.score?.toFixed(1)}
              </span>
              <span className="text-lg font-bold text-muted-foreground block">/10</span>
            </div>
          </motion.div>
        )}

        {/* Ready CTA */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.35 }}
          className="text-center text-sm font-semibold text-muted-foreground pb-2"
        >
          Ready for today? 🚀
        </motion.p>
      </div>
    </div>
  );
}