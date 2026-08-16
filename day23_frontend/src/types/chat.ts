export type ChatMessage = {
    role: 'user' | 'assistant'
    content: string
}

export type AgentRunResponse = {
    user_id: number
    question: string
    route: string
    answer: string | null
    tool_result: Record<string, unknown> | null
    sources?: Array<Record<string, unknown>>
}