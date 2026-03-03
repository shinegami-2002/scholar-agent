"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { ExternalLink, ChevronDown, ChevronUp, Calendar } from "lucide-react"
import { cn } from "@/lib/utils"
import type { PaperResult } from "@/lib/types"

interface PaperCardProps {
  paper: PaperResult
  index: number
}

export function PaperCard({ paper, index }: PaperCardProps) {
  const [expanded, setExpanded] = useState(false)

  const MAX_AUTHORS = 3
  const displayAuthors = paper.authors.slice(0, MAX_AUTHORS)
  const remainingAuthors = paper.authors.length - MAX_AUTHORS

  const ABSTRACT_LENGTH = 200
  const isLongAbstract = paper.abstract.length > ABSTRACT_LENGTH
  const displayAbstract = expanded
    ? paper.abstract
    : paper.abstract.slice(0, ABSTRACT_LENGTH) +
      (isLongAbstract ? "..." : "")

  const formattedDate = paper.published
    ? new Date(paper.published).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      })
    : null

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.08 }}
      className="group rounded-xl border border-white/[0.08] bg-white/[0.03] backdrop-blur-sm hover:border-white/15 hover:bg-white/[0.05] transition-all duration-300"
    >
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-2 mb-2">
          <a
            href={paper.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm font-semibold text-white/80 hover:text-white transition-colors flex items-start gap-1.5 flex-1"
          >
            <span className="flex-1">{paper.title}</span>
            <ExternalLink className="h-3.5 w-3.5 mt-0.5 shrink-0 opacity-0 group-hover:opacity-60 transition-opacity" />
          </a>
          <span
            className={cn(
              "shrink-0 text-[10px] font-medium px-2 py-0.5 rounded-full border",
              paper.source === "arxiv"
                ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
                : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
            )}
          >
            {paper.source === "arxiv" ? "arXiv" : "PubMed"}
          </span>
        </div>

        {/* Authors */}
        <p className="text-xs text-white/30 mb-2">
          {displayAuthors.join(", ")}
          {remainingAuthors > 0 && (
            <span className="text-white/20">
              {" "}
              +{remainingAuthors} more
            </span>
          )}
        </p>

        {/* Abstract */}
        <p className="text-xs text-white/40 leading-relaxed mb-2">
          {displayAbstract}
        </p>

        {isLongAbstract && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="inline-flex items-center gap-1 text-xs text-blue-400/70 hover:text-blue-400 transition-colors mb-2"
          >
            {expanded ? (
              <>
                Show less <ChevronUp className="h-3 w-3" />
              </>
            ) : (
              <>
                Show more <ChevronDown className="h-3 w-3" />
              </>
            )}
          </button>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-2 border-t border-white/5">
          {formattedDate && (
            <div className="flex items-center gap-1 text-[10px] text-white/25">
              <Calendar className="h-3 w-3" />
              {formattedDate}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}
