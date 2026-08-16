import { defineStore } from 'pinia'
import { ref } from 'vue'

import { runAgent } from '../api/agent'
import type { ActivityRecord } from '../types/activity'
import type { ChatMessage } from '../types/chat'

type AgentRunInput = {
  question: string
  userId?: number
  threadId?: string
}

const userId = 1
const threadId = 'frontend-chat-1'

const welcomeMessage: ChatMessage = {
  role: 'assistant',
  content: '你好，我是 Experiment Agent。你可以问我实验指标、工具调用或 Agent 学习相关问题。',
}

function sleep(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}

// 全局打字机控制器
let typingAbort: AbortController | null = null

export const useAgentStore = defineStore('agent', () => {
  const input = ref('')
  const messages = ref<ChatMessage[]>([{ ...welcomeMessage }])
  const loading = ref(false)
  const errorMessage = ref('')
  const activities = ref<ActivityRecord[]>([])

  // 中断正在进行的打字机
  function stopTyping() {
    if (typingAbort) {
      typingAbort.abort()
      typingAbort = null
    }
  }

  async function typeAssistantMessage(content: string) {
    stopTyping() // 开始新的打字前，先停掉旧的
    typingAbort = new AbortController()
    const signal = typingAbort.signal

    messages.value.push({
      role: 'assistant',
      content: '',
    })

    const messageIndex = messages.value.length - 1

    for (const char of content) {
      if (signal.aborted) return // 被中断了就立刻退出
      const currentMessage = messages.value[messageIndex]
      if (currentMessage) {
        currentMessage.content += char
      }
      await sleep(24)
    }

    typingAbort = null
  }

  function clearMessages() {
    stopTyping() // 清空时也停掉打字机
    messages.value = [{ ...welcomeMessage }]
    errorMessage.value = ''
  }

  async function sendMessage(payload?: AgentRunInput) {
    const question = (payload?.question ?? input.value).trim()

    if (!question || loading.value) {
      return
    }

    messages.value.push({
      role: 'user',
      content: question,
    })

    input.value = ''
    errorMessage.value = ''
    loading.value = true

    try {
      const data = await runAgent({
        user_id: payload?.userId ?? userId,
        question,
        thread_id: payload?.threadId ?? threadId,
        confirmed: false,
        request_id: `frontend-${Date.now()}`,
      })

      const answer = data.answer || '后端没有返回 answer。'

      activities.value.unshift({
        question,
        route: data.route,
        answer,
        toolResult: data.tool_result,
        sources: data.sources || [],
        createdAt: new Date().toLocaleString(),
      })

      loading.value = false
      await typeAssistantMessage(answer)
    } catch (error) {
      console.error(error)
      errorMessage.value = '请求失败，请检查后端是否启动，或查看浏览器控制台。'
      loading.value = false
      await typeAssistantMessage('抱歉，这次请求失败了。')
    }
  }

  return {
    input,
    messages,
    loading,
    errorMessage,
    activities,
    clearMessages,
    sendMessage,
    stopTyping,
  }
})