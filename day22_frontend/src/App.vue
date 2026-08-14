<script setup lang="ts">
import { nextTick, ref } from 'vue'

type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
}

type AgentRunResponse = {
  user_id: number
  question: string
  route: string
  answer: string | null
  tool_result: Record<string, unknown> | null
}

const userId = 1
const threadId = 'frontend-chat-1'

const welcomeMessage: ChatMessage = {
  role: 'assistant',
  content: '你好，我是 Experiment Agent。你可以问我实验指标、工具调用或 Agent 学习相关问题。',
}

const input = ref('')
const messages = ref<ChatMessage[]>([{ ...welcomeMessage }])
const loading = ref(false)
const errorMessage = ref('')
const messageListRef = ref<HTMLElement | null>(null)

function sleep(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}

async function scrollToBottom() {
  await nextTick()
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

async function typeAssistantMessage(content: string) {
  messages.value.push({
    role: 'assistant',
    content: '',
  })

  const messageIndex = messages.value.length - 1
  await scrollToBottom()

  for (const char of content) {
    const currentMessage = messages.value[messageIndex]

    if (currentMessage) {
      currentMessage.content += char
    }
    await scrollToBottom()
    await sleep(24)
  }
}

function clearMessages() {
  messages.value = [{ ...welcomeMessage }]
  errorMessage.value = ''
}

async function sendMessage() {
  const question = input.value.trim()

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
  await scrollToBottom()

  try {
    const response = await fetch('http://127.0.0.1:8000/agent/run', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        question,
        thread_id: threadId,
        confirmed: false,
        request_id: `frontend-${Date.now()}`,
      }),
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const data = (await response.json()) as AgentRunResponse
    const answer = data.answer || '后端没有返回 answer。'

    loading.value = false
    await typeAssistantMessage(answer)
  } catch (error) {
    console.error(error)
    errorMessage.value = '请求失败，请检查后端是否启动，或查看浏览器控制台。'

    loading.value = false
    await typeAssistantMessage('抱歉，这次请求失败了。')
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}
</script>

<template>
  <main class="page-shell">
    <section class="chat-panel">
      <header class="chat-header">
        <div>
          <h1>Experiment Agent</h1>
          <p>Agent workflow / RAG / Tool Calling</p>
        </div>
        <div class="header-actions">
          <button class="clear-button" type="button" @click="clearMessages">
            清空
          </button>
          <span class="status-pill">Day22</span>
        </div>
      </header>

      <div ref="messageListRef" class="message-list">
        <article
          v-for="(message, index) in messages"
          :key="index"
          class="message-row"
          :class="message.role"
        >
          <div class="message-bubble">
            <span class="message-role">
              {{ message.role === 'user' ? '你' : 'Agent' }}
            </span>
            <p>{{ message.content }}</p>
          </div>
        </article>

        <article v-if="loading" class="message-row assistant">
          <div class="message-bubble">
            <span class="message-role">Agent</span>
            <p>正在思考...</p>
          </div>
        </article>
      </div>

      <p v-if="errorMessage" class="error-text">
        {{ errorMessage }}
      </p>

      <footer class="composer">
        <textarea
          v-model="input"
          rows="3"
          placeholder="输入问题，例如：对比实验1和实验2的 F1"
          :disabled="loading"
          @keydown="handleKeydown"
        />
        <button :disabled="loading || !input.trim()" @click="sendMessage">
          {{ loading ? '发送中' : '发送' }}
        </button>
      </footer>
    </section>
  </main>
</template>

<style scoped>
.page-shell {
  min-height: 100vh;
  background: #eef2f5;
  color: #17202a;
  display: flex;
  justify-content: center;
  padding: 32px 16px;
}

.chat-panel {
  width: min(960px, 100%);
  height: calc(100vh - 64px);
  min-height: 640px;
  background: #ffffff;
  border: 1px solid #d8dee6;
  border-radius: 8px;
  display: grid;
  grid-template-rows: auto 1fr auto auto;
  overflow: hidden;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #e2e7ee;
  background: #fbfcfd;
}

.chat-header h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
}

.chat-header p {
  margin: 4px 0 0;
  color: #667085;
  font-size: 14px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.clear-button {
  border: 1px solid #cfd8e3;
  background: #ffffff;
  color: #344054;
  border-radius: 6px;
  padding: 7px 10px;
  font: inherit;
  font-size: 13px;
  cursor: pointer;
}

.clear-button:hover {
  background: #f2f4f7;
}

.status-pill {
  border: 1px solid #c7d7ef;
  background: #eef5ff;
  color: #245c9f;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 13px;
}

.message-list {
  padding: 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.message-row {
  display: flex;
}

.message-row.user {
  justify-content: flex-end;
}

.message-row.assistant {
  justify-content: flex-start;
}

.message-bubble {
  width: min(680px, 82%);
  border-radius: 8px;
  padding: 12px 14px;
  border: 1px solid #d9e1ea;
  background: #f7f9fb;
}

.message-row.user .message-bubble {
  background: #dff0ff;
  border-color: #b8daf7;
}

.message-role {
  display: block;
  margin-bottom: 6px;
  font-size: 12px;
  color: #667085;
  font-weight: 700;
}

.message-bubble p {
  margin: 0;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.error-text {
  margin: 0 24px 12px;
  padding: 10px 12px;
  border-radius: 6px;
  background: #fff1f0;
  border: 1px solid #ffccc7;
  color: #a8071a;
  font-size: 14px;
}

.composer {
  border-top: 1px solid #e2e7ee;
  padding: 16px;
  display: grid;
  grid-template-columns: 1fr 96px;
  gap: 12px;
  background: #fbfcfd;
}

.composer textarea {
  resize: none;
  border: 1px solid #cfd8e3;
  border-radius: 6px;
  padding: 12px;
  font: inherit;
  line-height: 1.5;
  outline: none;
}

.composer textarea:focus {
  border-color: #4b8fd8;
  box-shadow: 0 0 0 3px rgba(75, 143, 216, 0.16);
}

.composer textarea:disabled {
  background: #f2f4f7;
  cursor: not-allowed;
}

.composer button {
  border: 0;
  border-radius: 6px;
  background: #246bfe;
  color: #ffffff;
  font-weight: 700;
  cursor: pointer;
}

.composer button:disabled {
  background: #aeb8c5;
  cursor: not-allowed;
}

@media (max-width: 720px) {
  .page-shell {
    padding: 0;
  }

  .chat-panel {
    height: 100vh;
    min-height: 100vh;
    border-radius: 0;
    border: 0;
  }

  .chat-header {
    padding: 16px;
  }

  .message-list {
    padding: 16px;
  }

  .message-bubble {
    width: min(100%, 88%);
  }

  .composer {
    grid-template-columns: 1fr;
  }

  .composer button {
    min-height: 44px;
  }
}
</style>
