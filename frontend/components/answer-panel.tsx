"use client"

import { motion } from "framer-motion"
import ReactMarkdown from "react-markdown"
import { FileText } from "lucide-react"
import type { Citation } from "@/lib/types"

interface AnswerPanelProps {
  answer: string | null
  citations: Citation[]
}

export function AnswerPanel({ answer, citations }: AnswerPanelProps) {
  if (!answer) {
    return (
      <div className="rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-sm p-8">
        <div className="flex flex-col items-center justify-center text-center">
          <FileText className="h-12 w-12 text-white/10 mb-3" />
          <p className="text-sm text-white/30">
            Search for a research topic to get an AI-generated summary with
            citations.
          </p>
        </div>
      </div>
    )
  }

  const processedAnswer = answer.replace(
    /\[(\d+)\]/g,
    (match, num) => {
      const index = parseInt(num, 10)
      const citation = citations.find((c) => c.index === index)
      if (citation) {
        return `[\\[${num}\\]](${citation.url} "${citation.title}")`
      }
      return match
    }
  )

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-sm overflow-hidden"
    >
      <div className="px-5 py-4 border-b border-white/5 flex items-center gap-2">
        <FileText className="h-4 w-4 text-blue-400" />
        <h3 className="text-sm font-semibold text-white/80">Research Summary</h3>
      </div>

      <div className="px-5 py-4">
        <div className="prose-scholar text-sm leading-relaxed text-white/70">
          <ReactMarkdown
            components={{
              a: ({ href, children, title }) => {
                const text = String(children)
                const isCitation = /^\[\d+\]$/.test(text)

                if (isCitation) {
                  return (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      title={title || undefined}
                      className="inline-flex items-center justify-center min-w-[1.5rem] h-5 px-1 mx-0.5 text-xs font-semibold text-blue-400 bg-blue-500/15 rounded-md hover:bg-blue-500/25 transition-colors no-underline border border-blue-500/20"
                    >
                      {children}
                    </a>
                  )
                }

                return (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-400 hover:underline"
                  >
                    {children}
                  </a>
                )
              },
            }}
          >
            {processedAnswer}
          </ReactMarkdown>
        </div>

        {citations.length > 0 && (
          <div className="mt-6 pt-4 border-t border-white/5">
            <h4 className="text-[10px] font-semibold text-white/30 uppercase tracking-[0.2em] mb-2">
              References
            </h4>
            <ol className="space-y-1">
              {citations.map((citation) => (
                <li key={citation.index} className="text-xs">
                  <span className="text-blue-400 font-semibold mr-1">
                    [{citation.index}]
                  </span>
                  <a
                    href={citation.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-white/40 hover:text-white/70 transition-colors"
                  >
                    {citation.title}
                  </a>
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>
    </motion.div>
  )
}
