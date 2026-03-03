"use client"

import { motion } from "framer-motion"
import { BookOpen } from "lucide-react"
import { PaperCard } from "@/components/paper-card"
import type { PaperResult } from "@/lib/types"

interface SourceListProps {
  papers: PaperResult[]
}

export function SourceList({ papers }: SourceListProps) {
  if (papers.length === 0) return null

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4, delay: 0.2 }}
      className="space-y-3"
    >
      <div className="flex items-center gap-2">
        <BookOpen className="h-3.5 w-3.5 text-white/30" />
        <h3 className="text-xs font-semibold text-white/30 uppercase tracking-[0.2em]">
          Sources ({papers.length} paper{papers.length !== 1 ? "s" : ""})
        </h3>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {papers.map((paper, index) => (
          <PaperCard key={`${paper.url}-${index}`} paper={paper} index={index} />
        ))}
      </div>
    </motion.div>
  )
}
