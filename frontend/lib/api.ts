import { SearchRequest, SearchResponse, AgentStep } from "./types"

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export async function searchPapers(
  request: SearchRequest
): Promise<SearchResponse> {
  const response = await fetch(`${API_BASE_URL}/api/search`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    let message = `Search failed (${response.status})`
    try {
      const errorJson = await response.json()
      message = errorJson.detail || message
    } catch {
      message = await response.text()
    }
    if (response.status === 429) {
      throw new Error("Rate limit reached. Please wait 30 seconds and try again.")
    }
    throw new Error(message)
  }

  return response.json()
}

export interface WebSocketCallbacks {
  onStep: (step: AgentStep) => void
  onResult: (response: SearchResponse) => void
  onError: (error: string) => void
}

export function createSearchWebSocket(
  callbacks: WebSocketCallbacks
): {
  send: (request: SearchRequest) => void
  close: () => void
} {
  const wsUrl = API_BASE_URL.replace(/^http/, "ws")
  const ws = new WebSocket(`${wsUrl}/ws/search`)

  ws.onopen = () => {
    console.log("WebSocket connected")
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)

      if (data.type === "step") {
        callbacks.onStep(data.payload as AgentStep)
      } else if (data.type === "result") {
        callbacks.onResult(data.payload as SearchResponse)
      } else if (data.type === "error") {
        callbacks.onError(data.payload?.message || "Unknown error")
      }
    } catch (err) {
      callbacks.onError(`Failed to parse message: ${err}`)
    }
  }

  ws.onerror = () => {
    callbacks.onError("WebSocket connection error")
  }

  ws.onclose = () => {
    console.log("WebSocket disconnected")
  }

  return {
    send: (request: SearchRequest) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(request))
      } else {
        callbacks.onError("WebSocket is not connected")
      }
    },
    close: () => {
      ws.close()
    },
  }
}
