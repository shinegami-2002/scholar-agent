"use client"

import { motion } from "framer-motion"

export function Header() {
  return (
    <header className="w-full z-50 relative">
      <div className="container flex h-14 items-center justify-between px-4 md:px-8">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          className="flex items-center gap-2.5"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white">
            <span className="text-base font-black text-black tracking-tighter leading-none">S</span>
          </div>
          <span className="text-base font-bold tracking-tight text-white">
            ScholarAgent
          </span>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="flex items-center gap-3"
        >
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 backdrop-blur-sm">
            <div className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs text-white/60">Powered by Gemini</span>
          </div>
        </motion.div>
      </div>
    </header>
  )
}
