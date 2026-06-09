import React from "react";
import { Calendar, Video, Brain, Home } from "lucide-react";
import { motion } from "framer-motion";

export default function BottomNav({ activeTab, onTabChange }) {
  return (
    <div className="relative z-50 w-full px-5 pb-5 pt-2 bg-white">
      <div className="h-20 bg-white/80 backdrop-blur-xl border border-neutral-200 rounded-full flex items-center justify-between px-6 shadow-sm">
        {/* Home */}
        <motion.button
          whileTap={{ scale: 0.88 }}
          onClick={() => onTabChange("home")}
          className="flex flex-col items-center gap-1"
        >
          <Home
            className={`w-6 h-6 transition-colors duration-200 ${
              activeTab === "home" ? "text-black" : "text-neutral-400"
            }`}
            strokeWidth={activeTab === "home" ? 2.5 : 2}
          />
          <span
            className={`text-[10px] font-bold transition-colors duration-200 ${
              activeTab === "home" ? "text-black" : "text-neutral-400"
            }`}
          >
            Home
          </span>
        </motion.button>

        {/* Log */}
        <motion.button
          whileTap={{ scale: 0.88 }}
          onClick={() => onTabChange("log")}
          className="flex flex-col items-center gap-1"
        >
          <Calendar
            className={`w-6 h-6 transition-colors duration-200 ${
              activeTab === "log" ? "text-black" : "text-neutral-400"
            }`}
            strokeWidth={activeTab === "log" ? 2.5 : 2}
          />
          <span
            className={`text-[10px] font-bold transition-colors duration-200 ${
              activeTab === "log" ? "text-black" : "text-neutral-400"
            }`}
          >
            Log
          </span>
        </motion.button>

        {/* Camera — center hero button */}
        <motion.button
          whileTap={{ scale: 0.88 }}
          onClick={() => onTabChange("camera")}
          className="-mt-8 relative"
        >
          <div className="w-16 h-16 bg-black text-white rounded-full flex items-center justify-center shadow-[0_8px_24px_rgba(0,0,0,0.25)]">
            <Video className="w-7 h-7 text-white" strokeWidth={2} />
          </div>
        </motion.button>

        {/* Health */}
        <motion.button
          whileTap={{ scale: 0.88 }}
          onClick={() => onTabChange("health")}
          className="flex flex-col items-center gap-1"
        >
          <Brain
            className={`w-6 h-6 transition-colors duration-200 ${
              activeTab === "health" ? "text-black" : "text-neutral-400"
            }`}
            strokeWidth={activeTab === "health" ? 2.5 : 2}
          />
          <span
            className={`text-[10px] font-bold transition-colors duration-200 ${
              activeTab === "health" ? "text-black" : "text-neutral-400"
            }`}
          >
            Health
          </span>
        </motion.button>
      </div>
    </div>
  );
}