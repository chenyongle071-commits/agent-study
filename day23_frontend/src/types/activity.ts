export type ActivityRecord = {
    question: string
    route: string
    answer: string
    toolResult: Record<string, unknown> | null
    sources: Array<Record<string, unknown>>
    createdAt: string
}