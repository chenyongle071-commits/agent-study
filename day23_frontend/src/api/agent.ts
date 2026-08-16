import type { AgentRunResponse } from '../types/chat'
import { request } from '../utils/request'

type RunAgentRequest = {
  user_id: number
  question: string
  thread_id: string
  confirmed: boolean
  request_id: string
}

export function runAgent(data: RunAgentRequest) {
  return request<AgentRunResponse>('/agent/run', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}
