import React from "react";
import { motion } from "framer-motion";
import { Play, Pause, SkipForward, SkipBack } from "lucide-react";
import { format } from "date-fns";

export default function VideoPlayer({ date, clips }) {
  const [isPlaying, setIsPlaying] = React.useState(false);
  const [progress, setProgress] = React.useState(30);

  const timeMarkers = clips?.length > 0
    ? clips.map(c => c.time)
    : ["9:00 AM", "1:00 PM", "6:30 PM"];

  return (
    <motion.div
      initial={{ height: 0, opacity: 0 }}
      animate={{ height: "auto", opacity: 1 }}
      exit={{ height: 0, opacity: 0 }}
      transition={{ type: "spring", stiffness: 200, damping: 25 }}
      className="mb-6 overflow-hidden"
    >
      {/* Video area */}
      <div className="relative bg-zinc-900 rounded-3xl overflow-hidden aspect-video">
        <div className="absolute inset-0 bg-gradient-to-br from-zinc-800 via-zinc-900 to-black flex items-center justify-center">
          <div className="text-center">
            <div className="text-white/20 font-black text-4xl font-display mb-1">
              {format(date, "MMM d")}
            </div>
            <div className="text-white/10 font-bold text-sm">
              Stitched Vlog • {clips?.length || 3} clips
            </div>
          </div>
        </div>

        {/* Play overlay */}
        <motion.button
          whileTap={{ scale: 0.9 }}
          onClick={() => setIsPlaying(!isPlaying)}
          className="absolute inset-0 flex items-center justify-center"
        >
          <div className="w-16 h-16 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center">
            {isPlaying ? (
              <Pause className="w-7 h-7 text-white" fill="white" />
            ) : (
              <Play className="w-7 h-7 text-white ml-1" fill="white" />
            )}
          </div>
        </motion.button>
      </div>

      {/* Timeline scrubber */}
      <div className="mt-4 px-1">
        <div className="relative h-2 bg-secondary rounded-full overflow-hidden">
          <motion.div
            className="absolute left-0 top-0 h-full bg-foreground rounded-full"
            style={{ width: `${progress}%` }}
            animate={{ width: `${progress}%` }}
          />
          <input
            type="range"
            min={0}
            max={100}
            value={progress}
            onChange={(e) => setProgress(Number(e.target.value))}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />
        </div>

        {/* Time markers */}
        <div className="flex justify-between mt-2">
          {timeMarkers.map((t, i) => (
            <span key={i} className="text-[10px] font-bold text-muted-foreground">
              {t}
            </span>
          ))}
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-center gap-6 mt-3">
        <button className="w-9 h-9 rounded-full bg-secondary flex items-center justify-center">
          <SkipBack className="w-4 h-4" />
        </button>
        <motion.button
          whileTap={{ scale: 0.9 }}
          onClick={() => setIsPlaying(!isPlaying)}
          className="w-12 h-12 rounded-full bg-foreground flex items-center justify-center"
        >
          {isPlaying ? (
            <Pause className="w-5 h-5 text-background" fill="currentColor" />
          ) : (
            <Play className="w-5 h-5 text-background ml-0.5" fill="currentColor" />
          )}
        </motion.button>
        <button className="w-9 h-9 rounded-full bg-secondary flex items-center justify-center">
          <SkipForward className="w-4 h-4" />
        </button>
      </div>
    </motion.div>
  );
}