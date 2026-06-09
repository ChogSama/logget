import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, FlipVertical, Zap, Target } from "lucide-react";

export default function CameraScreen({ onClose }) {
  const [time, setTime] = useState(new Date());
  const [caption, setCaption] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [recordTime, setRecordTime] = useState(0);
  const intervalRef = useRef(null);

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (isRecording) {
      intervalRef.current = setInterval(() => {
        setRecordTime((prev) => {
          if (prev >= 5) {
            setIsRecording(false);
            clearInterval(intervalRef.current);
            return 0;
          }
          return prev + 1;
        });
      }, 1000);
    } else {
      clearInterval(intervalRef.current);
    }
    return () => clearInterval(intervalRef.current);
  }, [isRecording]);

  const hours = time.getHours().toString().padStart(2, "0");
  const minutes = time.getMinutes().toString().padStart(2, "0");

  return (
    <motion.div
      initial={{ opacity: 0, scale: 1.04 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.96 }}
      className="absolute inset-0 z-[60] bg-black flex flex-col rounded-[32px] overflow-hidden"
    >
      {/* Simulated camera background */}
      <div className="absolute inset-0 bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-950">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_60%_30%,rgba(255,255,255,0.04)_0%,transparent_70%)]" />
      </div>

      {/* Top bar: logo + controls */}
      <div className="relative z-10 flex items-center justify-between px-5 pt-8 pb-2">
        <motion.button
          whileTap={{ scale: 0.9 }}
          onClick={onClose}
          className="w-9 h-9 rounded-full bg-white/10 backdrop-blur-sm flex items-center justify-center"
        >
          <X className="w-4 h-4 text-white" />
        </motion.button>

        <span className="text-white font-black text-lg tracking-tighter">logget</span>

        <div className="flex gap-2">
          <button className="w-9 h-9 rounded-full bg-white/10 backdrop-blur-sm flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </button>
          <button className="w-9 h-9 rounded-full bg-white/10 backdrop-blur-sm flex items-center justify-center">
            <FlipVertical className="w-4 h-4 text-white" />
          </button>
        </div>
      </div>

      {/* Goal card */}
      <div className="relative z-10 mx-5 mt-2">
        <div className="bg-white/10 backdrop-blur-md rounded-2xl px-4 py-3">
          <div className="flex items-center gap-2 mb-2">
            <Target className="w-4 h-4 text-white/70" />
            <span className="text-white/70 text-xs font-bold">Target: 6-Pack in 3 Months</span>
          </div>
          <div className="relative h-2.5 bg-white/10 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: "42%" }}
              transition={{ duration: 1.2, ease: "easeOut", delay: 0.3 }}
              className="absolute left-0 top-0 h-full bg-white rounded-full"
            />
          </div>
          <span className="text-white/50 text-[10px] font-bold mt-1 block">42% complete</span>
        </div>
      </div>

      {/* Giant clock + date */}
      <div className="relative z-10 flex-1 flex flex-col items-center justify-center">
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.15 }}
          className="text-center"
        >
          <div className="text-white font-black text-8xl tracking-tight leading-none">
            {hours}:{minutes}
          </div>
          <div className="text-white/40 font-bold text-sm mt-2">
            {time.toLocaleDateString("en-US", { weekday: "long", month: "short", day: "numeric" })}
          </div>
        </motion.div>

        <AnimatePresence>
          {isRecording && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mt-6 flex items-center gap-2"
            >
              <div className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />
              <span className="text-white font-bold text-lg">{recordTime}s / 5s</span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Bottom area */}
      <div className="relative z-10 pb-8 px-5 space-y-5">
        {/* Caption input */}
        <div className="bg-white/20 backdrop-blur-md rounded-2xl px-5 py-3.5">
          <input
            type="text"
            placeholder="What's happening?..."
            value={caption}
            onChange={(e) => setCaption(e.target.value)}
            className="w-full bg-transparent text-white placeholder-white/40 font-semibold text-sm outline-none"
          />
        </div>

        {/* Record button */}
        <div className="flex justify-center">
          <motion.button
            whileTap={{ scale: 0.85 }}
            onClick={() => setIsRecording(!isRecording)}
            className="relative"
          >
            <div
              className={`w-20 h-20 rounded-full border-4 transition-colors duration-300 flex items-center justify-center ${
                isRecording ? "border-red-500" : "border-white"
              }`}
            >
              <motion.div
                animate={{
                  borderRadius: isRecording ? "8px" : "50%",
                  width: isRecording ? 28 : 56,
                  height: isRecording ? 28 : 56,
                }}
                transition={{ type: "spring", stiffness: 300, damping: 25 }}
                className={isRecording ? "bg-red-500" : "bg-white"}
              />
            </div>
            {isRecording && (
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="absolute inset-[-8px] rounded-full border-2 border-red-500/30 animate-pulse"
              />
            )}
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
}