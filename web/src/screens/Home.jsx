/**
 * @file Home.jsx
 * @description Shell của toàn bộ ứng dụng chính sau khi đăng nhập.
 * Quản lý tab navigation và fetch dữ liệu từ real API.
 *
 * Data flow:
 *   logs        → logsService.getLogs(selectedDateStr, timezone)   → LogTab
 *   overview    → dashboardService.getOverview(timezone)            → HomeTab
 *   insight     → insightsService.getDaily(selectedDateStr, tz)     → HealthTab
 *
 * NOTE: HomeTab, HealthTab, và LogTab (log management) cần cập nhật prop names
 * từ VlogEntry/DailyHealth mock shape sang LogResponse/OverviewResponse/DailyInsightResponse.
 * Search tags: logsService | dashboardService | insightsService | selectedDate | timezone
 */

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { AnimatePresence, motion } from "framer-motion";

import { logsService } from "@/services/logs.service";
import { dashboardService } from "@/services/dashboard.service";
import { insightsService } from "@/services/insights.service";

import BottomNav from "@/components/logget/BottomNav";
import CameraScreen from "@/components/logget/CameraScreen";
import LogTab from "@/screens/LogTab";
import HealthTab from "@/screens/HealthTab";
import HomeTab from "@/screens/HomeTab";

const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

export default function Home() {
  const [activeTab, setActiveTab] = useState("home");
  const [showCamera, setShowCamera] = useState(false);
  const [selectedDate, setSelectedDate] = useState(new Date());

  const selectedDateStr = format(selectedDate, "yyyy-MM-dd");

  const { data: logs = [] } = useQuery({
    queryKey: ["logs", selectedDateStr, timezone],
    queryFn: () => logsService.getLogs(selectedDateStr, timezone),
  });

  const { data: overview } = useQuery({
    queryKey: ["overview", timezone],
    queryFn: () => dashboardService.getOverview(timezone),
  });

  const { data: insight } = useQuery({
    queryKey: ["insight", selectedDateStr, timezone],
    queryFn: () => insightsService.getDaily(selectedDateStr, timezone),
  });

  const handleTabChange = (tab) => {
    if (tab === "camera") {
      setShowCamera(true);
    } else {
      setActiveTab(tab);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-200 flex items-center justify-center p-4">
      <div className="max-w-[400px] w-full h-[850px] mx-auto bg-white relative overflow-hidden rounded-[40px] border-[8px] border-black shadow-2xl flex flex-col">
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
                  logs={logs}
                  overview={overview}
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
                  logs={logs}
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
                  insight={insight}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <BottomNav activeTab={activeTab} onTabChange={handleTabChange} />

        <AnimatePresence>
          {showCamera && (
            <CameraScreen onClose={() => setShowCamera(false)} />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}