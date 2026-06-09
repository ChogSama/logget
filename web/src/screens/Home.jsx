import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { base44 } from "@/api/base44Client";
import { format } from "date-fns";
import { AnimatePresence, motion } from "framer-motion";
import BottomNav from "@/components/logget/BottomNav";
import CameraScreen from "@/components/logget/CameraScreen";
import LogTab from "@/pages/LogTab";
import HealthTab from "@/pages/HealthTab";
import HomeTab from "@/pages/HomeTab";

export default function Home() {
  const [activeTab, setActiveTab] = useState("home");
  const [showCamera, setShowCamera] = useState(false);
  const [selectedDate, setSelectedDate] = useState(new Date());

  const { data: vlogEntries = [] } = useQuery({
    queryKey: ["vlogs"],
    queryFn: () => base44.entities.VlogEntry.list("-created_date", 200),
  });

  const { data: healthEntries = [] } = useQuery({
    queryKey: ["health"],
    queryFn: () => base44.entities.DailyHealth.list("-created_date", 200),
  });

  const todayStr = format(new Date(), "yyyy-MM-dd");
  const selectedDateStr = format(selectedDate, "yyyy-MM-dd");
  const healthData = healthEntries.find((h) => h.date === selectedDateStr);
  const todayHealthData = healthEntries.find((h) => h.date === todayStr);

  const handleTabChange = (tab) => {
    if (tab === "camera") {
      setShowCamera(true);
    } else {
      setActiveTab(tab);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-200 flex items-center justify-center p-4">
      {/* Phone mockup */}
      <div className="max-w-[400px] w-full h-[850px] mx-auto bg-white relative overflow-hidden rounded-[40px] border-[8px] border-black shadow-2xl flex flex-col">
        {/* Scrollable content area */}
        <div className="flex-1 overflow-y-auto overflow-x-hidden">
          <AnimatePresence mode="wait">
            {activeTab === "home" && (
              <motion.div
                key="home"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -16 }}
                transition={{ duration: 0.22 }}
                className="min-h-full"
              >
                <HomeTab
                  vlogEntries={vlogEntries}
                  healthData={todayHealthData}
                  onOpenCamera={() => setShowCamera(true)}
                />
              </motion.div>
            )}

            {activeTab === "log" && (
              <motion.div
                key="log"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.22 }}
                className="min-h-full"
              >
                <LogTab
                  selectedDate={selectedDate}
                  setSelectedDate={setSelectedDate}
                  vlogEntries={vlogEntries}
                />
              </motion.div>
            )}

            {activeTab === "health" && (
              <motion.div
                key="health"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.22 }}
                className="min-h-full"
              >
                <HealthTab
                  selectedDate={selectedDate}
                  healthData={healthData}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Bottom Navigation — sits inside the phone */}
        <BottomNav activeTab={activeTab} onTabChange={handleTabChange} />

        {/* Camera Overlay — fills the phone */}
        <AnimatePresence>
          {showCamera && (
            <CameraScreen onClose={() => setShowCamera(false)} />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}