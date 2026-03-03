"use client"

import { useState, useCallback } from "react"
import { motion } from "framer-motion"
import { Header } from "@/components/header"
import { SearchBar } from "@/components/search-bar"
import { ThinkingSteps } from "@/components/thinking-steps"
import { AnswerPanel } from "@/components/answer-panel"
import { SourceList } from "@/components/source-list"
import { Skeleton } from "@/components/ui/skeleton"
import { EtheralShadow } from "@/components/ui/etheral-shadow"
import { RotatingText } from "@/components/ui/rotating-text"
import { searchPapers } from "@/lib/api"
import type {
  SearchRequest,
  SearchResponse,
  AgentStep,
} from "@/lib/types"

const ROTATING_WORDS = [
  "Research",
  "Papers",
  "Knowledge",
  "Science",
  "Discovery",
]

const ROTATING_COLORS = [
  "#60A5FA", // blue
  "#A78BFA", // purple
  "#34D399", // emerald
  "#F472B6", // pink
  "#FBBF24", // amber
]

export default function Home() {
  const [isLoading, setIsLoading] = useState(false)
  const [response, setResponse] = useState<SearchResponse | null>(null)
  const [steps, setSteps] = useState<AgentStep[]>([])
  const [error, setError] = useState<string | null>(null)

  const handleSearch = useCallback(async (request: SearchRequest) => {
    setIsLoading(true)
    setError(null)
    setResponse(null)
    setSteps([])

    const simulatedNodes = [
      { node: "Router", detail: `Classifying: "${request.query}"` },
      {
        node: "Retriever",
        detail: `Searching ${request.sources.join(", ")} for papers...`,
      },
      { node: "Grader", detail: "Evaluating paper relevance..." },
      { node: "Generator", detail: "Synthesizing research summary..." },
      { node: "HallucinationChecker", detail: "Verifying factual accuracy..." },
      { node: "Synthesizer", detail: "Formatting final response..." },
    ]

    const stepTimers: NodeJS.Timeout[] = []
    simulatedNodes.forEach((nodeInfo, index) => {
      const timer = setTimeout(() => {
        setSteps((prev) => {
          const updated = prev.map((s) =>
            s.status === "running"
              ? {
                  ...s,
                  status: "completed" as const,
                  duration_ms: 200 + Math.random() * 800,
                }
              : s
          )
          return [
            ...updated,
            {
              node: nodeInfo.node,
              status: "running" as const,
              detail: nodeInfo.detail,
              duration_ms: null,
            },
          ]
        })
      }, index * 600)
      stepTimers.push(timer)
    })

    try {
      const result = await searchPapers(request)
      stepTimers.forEach(clearTimeout)

      if (result.steps && result.steps.length > 0) {
        setSteps(result.steps)
      } else {
        setSteps(
          simulatedNodes.map((nodeInfo, i) => ({
            node: nodeInfo.node,
            status: "completed" as const,
            detail: nodeInfo.detail,
            duration_ms: 300 + i * 150,
          }))
        )
      }

      setResponse(result)
    } catch (err) {
      stepTimers.forEach(clearTimeout)
      const message =
        err instanceof Error ? err.message : "An unexpected error occurred"
      setError(message)

      // Mark all running/simulated steps as completed so nothing stays stuck
      setSteps((prev) =>
        prev.map((s) =>
          s.status === "running"
            ? { ...s, status: "completed" as const, detail: "Failed — " + message.slice(0, 60), duration_ms: 0 }
            : s
        )
      )
    } finally {
      setIsLoading(false)
    }
  }, [])

  const hasResults = isLoading || response || steps.length > 0

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex flex-col relative">
      {/* Ethereal Background — covers full page */}
      <div className="fixed inset-0 z-0">
        <EtheralShadow
          color="rgba(59, 130, 246, 0.6)"
          animation={{ scale: 80, speed: 60 }}
          noise={{ opacity: 0.8, scale: 1.2 }}
          sizing="fill"
        />
        {/* Dark overlay to keep content readable */}
        <div className="absolute inset-0 bg-[#0a0a0f]/70" />
      </div>

      {/* All content on top of background */}
      <div className="relative z-10 flex flex-col min-h-screen">
        <Header />

        {/* Hero / Search Section */}
        <section
          className={`px-4 transition-all duration-700 ease-in-out ${
            hasResults ? "py-6" : "py-16 md:py-24"
          }`}
        >
          {!hasResults && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="text-center mb-8"
            >
              <h2 className="text-3xl md:text-5xl lg:text-6xl font-bold mb-4 text-white">
                Search Academic{" "}
                <RotatingText
                  texts={ROTATING_WORDS}
                  colors={ROTATING_COLORS}
                  interval={2500}
                />
              </h2>
              <p className="text-sm md:text-base text-white/40 max-w-xl mx-auto leading-relaxed">
                AI agent that searches arXiv & PubMed, grades relevance,
                and generates cited summaries with hallucination checking.
              </p>
            </motion.div>
          )}

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            <SearchBar onSearch={handleSearch} isLoading={isLoading} />
          </motion.div>
        </section>

        {/* Error Banner */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="container max-w-6xl px-4 mb-4"
          >
            <div className="rounded-xl border border-red-500/30 bg-red-500/10 backdrop-blur-sm p-4 text-sm text-red-300">
              <strong>Error:</strong> {error}
            </div>
          </motion.div>
        )}

        {/* Results Section */}
        {hasResults && (
          <motion.section
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4 }}
            className="flex-1 container max-w-6xl px-4 pb-12"
          >
            <div className="grid grid-cols-1 md:grid-cols-[260px_1fr] gap-6">
              {/* Left Column: Agent Pipeline */}
              <aside className="order-2 md:order-1">
                {isLoading && steps.length === 0 ? (
                  <div className="space-y-3">
                    <Skeleton className="h-4 w-32 bg-white/5" />
                    <Skeleton className="h-10 w-full bg-white/5 rounded-xl" />
                    <Skeleton className="h-10 w-full bg-white/5 rounded-xl" />
                    <Skeleton className="h-10 w-full bg-white/5 rounded-xl" />
                  </div>
                ) : (
                  <ThinkingSteps steps={steps} />
                )}

                {response && response.rewrite_count > 0 && (
                  <div className="mt-4 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 backdrop-blur-sm">
                    <p className="text-xs text-amber-300">
                      Query was rewritten{" "}
                      <span className="font-semibold">
                        {response.rewrite_count}
                      </span>{" "}
                      time{response.rewrite_count > 1 ? "s" : ""} for better
                      results.
                    </p>
                  </div>
                )}
              </aside>

              {/* Right Column: Answer + Sources */}
              <main className="order-1 md:order-2 space-y-6">
                {isLoading && !response ? (
                  <div className="space-y-4">
                    <Skeleton className="h-6 w-48 bg-white/5" />
                    <Skeleton className="h-4 w-full bg-white/5" />
                    <Skeleton className="h-4 w-full bg-white/5" />
                    <Skeleton className="h-4 w-3/4 bg-white/5" />
                    <Skeleton className="h-4 w-full bg-white/5" />
                    <Skeleton className="h-4 w-5/6 bg-white/5" />
                    <div className="pt-4">
                      <Skeleton className="h-5 w-36 mb-3 bg-white/5" />
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                        <Skeleton className="h-40 w-full rounded-xl bg-white/5" />
                        <Skeleton className="h-40 w-full rounded-xl bg-white/5" />
                      </div>
                    </div>
                  </div>
                ) : (
                  <>
                    <AnswerPanel
                      answer={response?.answer || null}
                      citations={response?.citations || []}
                    />
                    <SourceList papers={response?.papers || []} />
                  </>
                )}
              </main>
            </div>
          </motion.section>
        )}

        {/* Footer */}
        <footer className="mt-auto py-4 relative">
          <div className="container text-center">
            <p className="text-xs text-white/20">
              ScholarAgent -- Built with LangGraph, ChromaDB, FastAPI & Next.js
            </p>
          </div>
        </footer>
      </div>
    </div>
  )
}
