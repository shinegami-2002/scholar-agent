"use client"

import { useState } from "react"
import {
  CheckCircle2,
  Loader2,
  SkipForward,
  Brain,
  Search,
  FileCheck,
  RefreshCw,
  PenLine,
  ShieldCheck,
  Sparkles,
  ChevronUp,
  Activity,
} from "lucide-react"
import { cn } from "@/lib/utils"
import type { AgentStep } from "@/lib/types"

interface ThinkingStepsProps {
  steps: AgentStep[]
}

const NODE_CONFIG: Record<
  string,
  { label: string; icon: React.ElementType }
> = {
  Router: { label: "Classifying Query", icon: Brain },
  router: { label: "Classifying Query", icon: Brain },
  Retriever: { label: "Searching Papers", icon: Search },
  retriever: { label: "Searching Papers", icon: Search },
  Grader: { label: "Grading Relevance", icon: FileCheck },
  grader: { label: "Grading Relevance", icon: FileCheck },
  Rewriter: { label: "Rewriting Query", icon: RefreshCw },
  rewriter: { label: "Rewriting Query", icon: RefreshCw },
  Generator: { label: "Generating Answer", icon: PenLine },
  generator: { label: "Generating Answer", icon: PenLine },
  HallucinationChecker: { label: "Checking Accuracy", icon: ShieldCheck },
  hallucination_checker: { label: "Checking Accuracy", icon: ShieldCheck },
  Synthesizer: { label: "Formatting Response", icon: Sparkles },
  synthesizer: { label: "Formatting Response", icon: Sparkles },
}

function getNodeConfig(nodeName: string) {
  return (
    NODE_CONFIG[nodeName] || {
      label: nodeName,
      icon: Brain,
    }
  )
}

function formatDuration(ms: number | null): string {
  if (ms === null || ms === 0) return ""
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

export function ThinkingSteps({ steps }: ThinkingStepsProps) {
  const [isOpen, setIsOpen] = useState(true)

  if (steps.length === 0) return null

  const completedCount = steps.filter(
    (s) => s.status === "completed" || s.status === "skipped"
  ).length
  const isRunning = steps.some((s) => s.status === "running")

  return (
    <div
      className={cn(
        "w-full rounded-2xl overflow-hidden cursor-pointer select-none",
        "bg-neutral-900",
        "shadow-xl shadow-black/30",
        "transition-all duration-500 ease-[cubic-bezier(0.4,0,0.2,1)]",
        isOpen ? "rounded-3xl" : "rounded-2xl"
      )}
      onClick={() => setIsOpen(!isOpen)}
    >
      {/* Header */}
      <div className="flex items-center gap-3 p-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-neutral-800 transition-colors duration-300">
          {isRunning ? (
            <Loader2 className="h-4 w-4 text-neutral-300 animate-spin" />
          ) : (
            <Activity className="h-4 w-4 text-neutral-300" />
          )}
        </div>
        <div className="flex-1 overflow-hidden">
          <h3 className="text-sm font-semibold text-white">
            {isRunning
              ? `Running Agent Pipeline...`
              : `${completedCount} Steps Completed`}
          </h3>
          <p
            className={cn(
              "text-xs text-neutral-400",
              "transition-all duration-500 ease-[cubic-bezier(0.4,0,0.2,1)]",
              isOpen
                ? "opacity-0 max-h-0 mt-0"
                : "opacity-100 max-h-6 mt-0.5"
            )}
          >
            {isRunning ? "Processing your query" : "Click to view details"}
          </p>
        </div>
        <div className="flex h-8 w-8 items-center justify-center">
          <ChevronUp
            className={cn(
              "h-4 w-4 text-neutral-500 transition-transform duration-500 ease-[cubic-bezier(0.4,0,0.2,1)]",
              isOpen ? "rotate-0" : "rotate-180"
            )}
          />
        </div>
      </div>

      {/* Step List */}
      <div
        className={cn(
          "grid",
          "transition-all duration-500 ease-[cubic-bezier(0.4,0,0.2,1)]",
          isOpen
            ? "grid-rows-[1fr] opacity-100"
            : "grid-rows-[0fr] opacity-0"
        )}
      >
        <div className="overflow-hidden">
          <div className="px-2 pb-3">
            <div className="space-y-0.5">
              {steps.map((step, index) => {
                const config = getNodeConfig(step.node)
                const NodeIcon = config.icon
                const isStepRunning = step.status === "running"
                const isCompleted = step.status === "completed"
                const isSkipped = step.status === "skipped"

                return (
                  <div
                    key={`${step.node}-${index}`}
                    className={cn(
                      "flex items-start gap-3 rounded-xl p-3",
                      "transition-all duration-500 ease-[cubic-bezier(0.4,0,0.2,1)]",
                      isStepRunning && "bg-neutral-800/60",
                      !isStepRunning && "hover:bg-neutral-800/30",
                      isOpen
                        ? "translate-y-0 opacity-100"
                        : "translate-y-4 opacity-0"
                    )}
                    style={{
                      transitionDelay: isOpen ? `${index * 60}ms` : "0ms",
                    }}
                    onClick={(e) => e.stopPropagation()}
                  >
                    {/* Icon */}
                    <div
                      className={cn(
                        "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl transition-colors duration-300",
                        isStepRunning && "bg-neutral-700",
                        isCompleted && "bg-neutral-800",
                        isSkipped && "bg-neutral-800/50"
                      )}
                    >
                      {isStepRunning ? (
                        <Loader2 className="h-4 w-4 text-white animate-spin" />
                      ) : isCompleted ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                      ) : (
                        <SkipForward className="h-4 w-4 text-neutral-500" />
                      )}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <NodeIcon
                          className={cn(
                            "h-3.5 w-3.5",
                            isStepRunning && "text-neutral-300",
                            isCompleted && "text-neutral-400",
                            isSkipped && "text-neutral-600"
                          )}
                        />
                        <h4
                          className={cn(
                            "text-sm font-medium",
                            isStepRunning && "text-white",
                            isCompleted && "text-neutral-200",
                            isSkipped && "text-neutral-500"
                          )}
                        >
                          {config.label}
                        </h4>
                      </div>
                      {step.detail && (
                        <p className="text-xs text-neutral-500 truncate mt-0.5">
                          {step.detail}
                        </p>
                      )}
                    </div>

                    {/* Duration */}
                    <span className="text-[10px] font-mono text-neutral-600 shrink-0 pt-1">
                      {formatDuration(step.duration_ms)}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
