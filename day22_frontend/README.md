# Day22 Vue 对话页面

## 今日目标

- 完成 Vue 前端对话页面
- 调用后端 Agent 接口
- 展示用户消息和 Agent 回复
- 实现加载状态
- 实现错误状态
- 实现模拟流式输出
- 保留当前页面内的历史消息
- 支持清空当前会话

## 项目结构

```text
day22_frontend/
├── src/
│   ├── App.vue
│   └── main.ts
├── package.json
├── vite.config.ts
└── README.md

启动方式
先启动后端：
cd D:\agent_study\day21
D:\agent_study\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
再启动前端：
cd D:\agent_study\day22_frontend
npm run dev
浏览器访问：
http://localhost:5173
前后端请求流程
用户在 Vue 页面输入问题。
前端通过 fetch 请求后端：
POST http://127.0.0.1:8000/agent/run
请求体示例：
{
  "user_id": 1,
  "question": "查询实验1的信息",
  "thread_id": "frontend-chat-1",
  "confirmed": false,
  "request_id": "frontend-1720000000000"
}
后端根据问题选择 Agent 路由和工具，返回回答。
前端把后端返回的 answer 展示到聊天窗口中。
页面状态
messages
messages 用来保存当前页面里的聊天消息。
每条消息包含：
type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
}
role 决定消息显示在左侧还是右侧。
content 是真正展示的文本内容。
loading
loading 表示当前是否正在请求后端。
请求开始时：
loading.value = true
请求结束后：
loading.value = false
它主要用于：
禁用输入框
禁用发送按钮
显示“正在思考...”
errorMessage
errorMessage 用来保存错误提示。
比如后端没有启动、接口报错、网络失败时，前端会展示错误状态。
模拟流式输出
这次没有直接使用真正的 SSE 流式接口，而是在前端做了一个模拟流式输出。
核心逻辑是：
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
它的意思是：
先创建一条空的 Agent 消息。
然后把后端返回的完整回答拆成一个个字符。
每隔一小段时间追加一个字符。
这样用户看到的效果就是 Agent 正在逐字输出。
自动滚动
前端通过 ref 拿到消息列表 DOM：
const messageListRef = ref<HTMLElement | null>(null)
每次新增消息或追加字符后，调用：
async function scrollToBottom() {
  await nextTick()

  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}
这样聊天内容变多时，页面会自动滚动到底部。
清空会话
页面右上角增加了“清空”按钮。
点击后会执行：
function clearMessages() {
  messages.value = [{ ...welcomeMessage }]
  errorMessage.value = ''
}
这个功能只会清空前端页面中的临时消息，不会删除后端数据库里的历史记录。
CORS 问题
前端运行在：
http://localhost:5173
后端运行在：
http://127.0.0.1:8000
它们端口不同，所以浏览器会认为这是跨域请求。
因此后端需要允许前端访问。
在 FastAPI 中加入：
from fastapi.middleware.cors import CORSMiddleware
并配置：
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
这样 Vue 前端才能正常请求 FastAPI 后端。
今日理解
Vue 前端主要负责用户交互。
FastAPI 后端主要负责业务逻辑、Agent 工作流、工具调用和数据库操作。
Day22 把前端和后端真正连接了起来：
用户输入
-> Vue 保存用户消息
-> fetch 调用 FastAPI
-> FastAPI 调用 Agent 工作流
-> Agent 返回 answer
-> Vue 展示 Agent 回复
这一步之后，项目不再只是后端接口，而是有了一个可以实际操作的聊天页面。
```