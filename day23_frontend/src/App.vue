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
  sources?: Array<Record<string, unknown>>
}

type ActivityRecord = {
  question: string
  route: string
  answer: string
  toolResult: Record<string, unknown> | null
  sources: Array<Record<string, unknown>>
  createdAt: string
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
const activities = ref<ActivityRecord[]>([])

type ActiveTab = 'chat' | 'experiments' | 'activity'

const activeTab = ref<ActiveTab>('chat')

type Experiment = {
  id: number
  name: string
  modelName: string
  datasetName: string
  accuracy: number
  f1: number
  latencyMs: number
  cost: number
  status: string
}

const experiments = ref<Experiment[]>([
  {
    id: 1,
    name: '实验1',
    modelName: 'deepseek-chat',
    datasetName: 'eval-set-a',
    accuracy: 0.91,
    f1: 0.87,
    latencyMs: 820,
    cost: 1.24,
    status: 'completed',
  },
  {
    id: 2,
    name: '实验2',
    modelName: 'deepseek-chat',
    datasetName: 'eval-set-b',
    accuracy: 0.88,
    f1: 0.82,
    latencyMs: 960,
    cost: 1.41,
    status: 'completed',
  },
  {
    id: 3,
    name: '实验3',
    modelName: 'qwen-plus',
    datasetName: 'eval-set-a',
    accuracy: 0.84,
    f1: 0.79,
    latencyMs: 730,
    cost: 1.08,
    status: 'running',
  },
])

const maxF1 = 1

function sleep(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}

async function scrollToBottom() {
  await nextTick()
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

function getSelectedTool(toolResult: Record<string, unknown> | null) {
  if (!toolResult) {
    return ''
  }

  const selectedTool = toolResult.selected_tool

  return typeof selectedTool === 'string' ? selectedTool : ''
}

function getExperimentDetail(toolResult: Record<string, unknown> | null) {
  if (!toolResult) {
    return null
  }

  const rawToolResult = toolResult.tool_result

  if (!rawToolResult || typeof rawToolResult !== 'object') {
    return null
  }

  return rawToolResult as {
    id?: number
    user_id?: number
    name?: string
    model_name?: string
    dataset_name?: string
    accuracy?: number
    f1?: number
    latency_ms?: number
    cost?: number
    status?: string
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
          <button
            class="tab-button"
            :class="{ active: activeTab === 'chat' }"
            type="button"
            @click="activeTab = 'chat'"
          >
            对话
          </button>
          <button
            class="tab-button"
            :class="{ active: activeTab === 'experiments' }"
            type="button"
            @click="activeTab = 'experiments'"
          >
            实验管理
          </button>
          <button
            class="tab-button"
            :class="{ active: activeTab === 'activity' }"
            type="button"
            @click="activeTab = 'activity'"
          >
            执行过程
          </button>
          <span class="status-pill">Day23</span>
        </div>
      </header>

      <template v-if="activeTab === 'chat'">
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
          <div class="composer-actions">
            <button class="clear-button" type="button" @click="clearMessages">
              清空
            </button>
            <button :disabled="loading || !input.trim()" @click="sendMessage">
              {{ loading ? '发送中' : '发送' }}
            </button>
          </div>
        </footer>
      </template>

      <section v-else-if="activeTab === 'experiments'" class="workspace-panel">
        <div class="panel-header">
          <h2>实验管理</h2>
          <p>查看实验列表，并快速比较不同实验的核心指标。</p>
        </div>

        <div class="metric-summary">
          <div>
            <span>实验数量</span>
            <strong>{{ experiments.length }}</strong>
          </div>
          <div>
            <span>最高 F1</span>
            <strong>{{ Math.max(...experiments.map((item) => item.f1)).toFixed(2) }}</strong>
          </div>
          <div>
            <span>最低延迟</span>
            <strong>{{ Math.min(...experiments.map((item) => item.latencyMs)) }} ms</strong>
          </div>
        </div>

        <div class="table-wrap">
          <table class="experiment-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>实验名称</th>
                <th>模型</th>
                <th>数据集</th>
                <th>Accuracy</th>
                <th>F1</th>
                <th>Latency</th>
                <th>Cost</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="experiment in experiments" :key="experiment.id">
                <td>{{ experiment.id }}</td>
                <td>{{ experiment.name }}</td>
                <td>{{ experiment.modelName }}</td>
                <td>{{ experiment.datasetName }}</td>
                <td>{{ experiment.accuracy.toFixed(2) }}</td>
                <td>{{ experiment.f1.toFixed(2) }}</td>
                <td>{{ experiment.latencyMs }} ms</td>
                <td>{{ experiment.cost.toFixed(2) }}</td>
                <td>
                  <span class="status-tag" :class="experiment.status">
                    {{ experiment.status }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="chart-panel">
          <h3>F1 指标对比</h3>

          <div
            v-for="experiment in experiments"
            :key="experiment.id"
            class="bar-row"
          >
            <span class="bar-label">{{ experiment.name }}</span>
            <div class="bar-track">
              <div
                class="bar-fill"
                :style="{ width: `${(experiment.f1 / maxF1) * 100}%` }"
              />
            </div>
            <strong>{{ experiment.f1.toFixed(2) }}</strong>
          </div>
        </div>
      </section>

      <section v-else class="workspace-panel">
        <div class="panel-header">
          <h2>执行过程</h2>
          <p>查看最近的 Agent 路由、工具调用结果和引用来源。</p>
        </div>

        <div v-if="activities.length === 0" class="empty-state">
          当前还没有执行记录。回到“对话”发送一个问题后，这里会显示处理过程。
        </div>

        <div v-else class="activity-list">
          <article
            v-for="(activity, index) in activities"
            :key="`${activity.createdAt}-${index}`"
            class="activity-card"
          >
            <div class="activity-card-header">
              <div>
                <span class="activity-time">{{ activity.createdAt }}</span>
                <h3>{{ activity.question }}</h3>
              </div>
              <span class="route-tag">{{ activity.route }}</span>
            </div>

            <div class="activity-section">
              <h4>Agent 回答</h4>
              <p>{{ activity.answer }}</p>
            </div>

            <div class="activity-section">
              <h4>工具结果</h4>

              <div v-if="getExperimentDetail(activity.toolResult)" class="tool-detail">
                <div>
                  <span>调用工具</span>
                  <strong>{{ getSelectedTool(activity.toolResult) }}</strong>
                </div>
                <div>
                  <span>实验名称</span>
                  <strong>{{ getExperimentDetail(activity.toolResult)?.name }}</strong>
                </div>
                <div>
                  <span>模型</span>
                  <strong>{{ getExperimentDetail(activity.toolResult)?.model_name }}</strong>
                </div>
                <div>
                  <span>数据集</span>
                  <strong>{{ getExperimentDetail(activity.toolResult)?.dataset_name }}</strong>
                </div>
                <div>
                  <span>Accuracy</span>
                  <strong>{{ getExperimentDetail(activity.toolResult)?.accuracy }}</strong>
                </div>
                <div>
                  <span>F1</span>
                  <strong>{{ getExperimentDetail(activity.toolResult)?.f1 }}</strong>
                </div>
                <div>
                  <span>Latency</span>
                  <strong>{{ getExperimentDetail(activity.toolResult)?.latency_ms }} ms</strong>
                </div>
                <div>
                  <span>Cost</span>
                  <strong>{{ getExperimentDetail(activity.toolResult)?.cost }}</strong>
                </div>
                <div>
                  <span>状态</span>
                  <strong>{{ getExperimentDetail(activity.toolResult)?.status }}</strong>
                </div>
              </div>

              <pre v-else>{{ JSON.stringify(activity.toolResult, null, 2) }}</pre>
            </div>

            <div class="activity-section">
              <h4>引用来源</h4>

              <div v-if="activity.sources.length === 0" class="source-empty">
                本次没有返回引用来源。
              </div>

              <ul v-else class="source-list">
                <li
                  v-for="(source, sourceIndex) in activity.sources"
                  :key="sourceIndex"
                >
                  <pre>{{ JSON.stringify(source, null, 2) }}</pre>
                </li>
              </ul>
            </div>
          </article>
        </div>
      </section>
    </section>
  </main>
</template>

<style scoped>
.activity-list {
  margin-top: 20px;
  display: grid;
  gap: 16px;
}

.activity-card {
  border: 1px solid #d9e1ea;
  border-radius: 8px;
  background: #ffffff;
  padding: 16px;
}

.activity-card-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.activity-time {
  color: #667085;
  font-size: 12px;
}

.activity-card h3 {
  margin: 6px 0 0;
  font-size: 16px;
}

.route-tag {
  border: 1px solid #b8daf7;
  background: #eaf4ff;
  color: #155eef;
  border-radius: 999px;
  padding: 4px 8px;
  font-size: 12px;
  white-space: nowrap;
}

.activity-section {
  margin-top: 14px;
}

.activity-section h4 {
  margin: 0 0 8px;
  font-size: 14px;
  color: #475467;
}

.activity-section p {
  margin: 0;
  line-height: 1.7;
}

.activity-section pre,
.source-list pre {
  margin: 0;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
  border-radius: 6px;
  background: #f8fafc;
  border: 1px solid #e4e9f0;
  padding: 10px;
  font-size: 12px;
  line-height: 1.6;
}

.source-empty {
  color: #667085;
  border: 1px dashed #cfd8e3;
  border-radius: 6px;
  padding: 10px;
  background: #f8fafc;
}

.source-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 10px;
}

.metric-summary {
  margin-top: 20px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}

.metric-summary div {
  border: 1px solid #d9e1ea;
  border-radius: 8px;
  padding: 14px;
  background: #f8fafc;
}

.metric-summary span {
  display: block;
  color: #667085;
  font-size: 13px;
}

.metric-summary strong {
  display: block;
  margin-top: 8px;
  font-size: 22px;
}

.table-wrap {
  margin-top: 20px;
  overflow-x: auto;
  border: 1px solid #d9e1ea;
  border-radius: 8px;
}

.experiment-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  background: #ffffff;
}

.experiment-table th,
.experiment-table td {
  padding: 12px;
  border-bottom: 1px solid #e4e9f0;
  text-align: left;
  white-space: nowrap;
}

.experiment-table th {
  background: #f8fafc;
  color: #475467;
  font-weight: 700;
}

.experiment-table tr:last-child td {
  border-bottom: 0;
}

.status-tag {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 8px;
  font-size: 12px;
  border: 1px solid #d0d5dd;
  background: #f2f4f7;
  color: #344054;
}

.status-tag.completed {
  border-color: #abefc6;
  background: #ecfdf3;
  color: #067647;
}

.status-tag.running {
  border-color: #fedf89;
  background: #fffaeb;
  color: #b54708;
}

.chart-panel {
  margin-top: 20px;
  border: 1px solid #d9e1ea;
  border-radius: 8px;
  padding: 16px;
  background: #ffffff;
}

.chart-panel h3 {
  margin: 0 0 16px;
  font-size: 16px;
}

.bar-row {
  display: grid;
  grid-template-columns: 72px 1fr 48px;
  gap: 12px;
  align-items: center;
  margin-top: 12px;
}

.bar-label {
  color: #475467;
  font-size: 14px;
}

.bar-track {
  height: 12px;
  border-radius: 999px;
  background: #e4e9f0;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 999px;
  background: #2f6fed;
}

.bar-row strong {
  font-size: 14px;
  text-align: right;
}

@media (max-width: 720px) {
  .metric-summary {
    grid-template-columns: 1fr;
  }
}

.tab-button {
  border: 1px solid #cfd8e3;
  background: #ffffff;
  color: #344054;
  border-radius: 6px;
  padding: 7px 10px;
  font: inherit;
  font-size: 13px;
  cursor: pointer;
}

.tab-button:hover {
  background: #f2f4f7;
}

.tab-button.active {
  border-color: #8bbcf3;
  background: #eaf4ff;
  color: #155eef;
}

.composer-actions {
  display: grid;
  grid-template-rows: 1fr 1fr;
  gap: 8px;
}

.workspace-panel {
  padding: 24px;
  overflow-y: auto;
}

.panel-header h2 {
  margin: 0;
  font-size: 20px;
}

.panel-header p {
  margin: 8px 0 0;
  color: #667085;
}

.empty-state {
  margin-top: 20px;
  padding: 24px;
  border: 1px dashed #cfd8e3;
  border-radius: 8px;
  color: #667085;
  background: #f8fafc;
}

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

.tool-detail {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.tool-detail div {
  border: 1px solid #e4e9f0;
  border-radius: 6px;
  background: #f8fafc;
  padding: 10px;
}

.tool-detail span {
  display: block;
  color: #667085;
  font-size: 12px;
}

.tool-detail strong {
  display: block;
  margin-top: 6px;
  color: #17202a;
  font-size: 14px;
  word-break: break-word;
}

@media (max-width: 720px) {
  .tool-detail {
    grid-template-columns: 1fr;
  }
}
</style>
