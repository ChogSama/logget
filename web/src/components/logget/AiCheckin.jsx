import React, { useState } from "react";
import { motion } from "framer-motion";
import { Bot, ThumbsUp, ThumbsDown } from "lucide-react";
import { Button } from "@/components/ui/button";

const defaultMessages = [
  { role: "ai", text: "I noticed from the vlog you skipped lunch today. Was it because you were too busy?" },
  { role: "user", text: "Yeah, the hackathon deadline was too tight." },
  { role: "ai", text: "Got it. Skipping meals tanks your energy. Let's try a quick 10-min prep tomorrow. Want a fast healthy recipe?" },
];

export default function AiCheckin({ messages }) {
  const displayMessages = messages?.length > 0 ? messages : defaultMessages;
  const [feedback, setFeedback] = useState(null);
  const [showRecipe, setShowRecipe] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
      className="border border-border rounded-3xl p-5"
    >
      <div className="flex items-center gap-2 mb-5">
        <div className="w-8 h-8 rounded-full bg-foreground flex items-center justify-center">
          <Bot className="w-4 h-4 text-background" />
        </div>
        <span className="text-sm font-black font-display">AI Check-in</span>
      </div>

      <div className="space-y-3 mb-5">
        {displayMessages.map((msg, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: msg.role === "user" ? 20 : -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 + i * 0.15 }}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] px-4 py-3 text-sm font-semibold leading-relaxed ${
                msg.role === "user"
                  ? "bg-foreground text-background rounded-3xl rounded-br-lg"
                  : "bg-secondary text-foreground rounded-3xl rounded-bl-lg"
              }`}
            >
              {msg.text}
            </div>
          </motion.div>
        ))}

        {showRecipe && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex justify-start"
          >
            <div className="max-w-[85%] px-4 py-3 text-sm font-semibold leading-relaxed bg-secondary text-foreground rounded-3xl rounded-bl-lg">
              🍚 <strong>Quick Rice Bowl</strong>: Microwave rice (2 min) + canned tuna + soy sauce + sesame oil. Done in under 10 min!
            </div>
          </motion.div>
        )}
      </div>

      {/* Action Buttons */}
      {!showRecipe && (
        <div className="flex gap-2 mb-4">
          <Button
            className="flex-1 rounded-full font-bold text-sm h-11"
            onClick={() => setShowRecipe(true)}
          >
            Show Recipe
          </Button>
          <Button
            variant="outline"
            className="flex-1 rounded-full font-bold text-sm h-11 border-2"
          >
            Maybe later
          </Button>
        </div>
      )}

      {/* Feedback Buttons */}
      <div className="pt-4 border-t border-border">
        <p className="text-xs font-bold text-muted-foreground mb-3">Was this advice helpful?</p>
        <div className="flex gap-2">
          <button
            onClick={() => setFeedback("helpful")}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-full border-2 text-xs font-bold transition-all ${
              feedback === "helpful"
                ? "bg-foreground text-background border-foreground"
                : "border-border text-muted-foreground hover:border-foreground/40"
            }`}
          >
            <ThumbsUp className="w-3.5 h-3.5" />
            Helpful
          </button>
          <button
            onClick={() => setFeedback("not_helpful")}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-full border-2 text-xs font-bold transition-all ${
              feedback === "not_helpful"
                ? "bg-foreground text-background border-foreground"
                : "border-border text-muted-foreground hover:border-foreground/40"
            }`}
          >
            <ThumbsDown className="w-3.5 h-3.5" />
            Not Helpful
          </button>
          {feedback && (
            <motion.span
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              className="text-xs font-semibold text-muted-foreground self-center ml-1"
            >
              Thanks! 🙏
            </motion.span>
          )}
        </div>
      </div>
    </motion.div>
  );
}