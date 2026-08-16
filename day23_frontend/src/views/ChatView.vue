<script setup lang="ts">
defineOptions({ name: 'ChatView' })

import { storeToRefs } from 'pinia'
import { onBeforeRouteLeave } from 'vue-router'
import { useAgentStore } from '../stores/agent'

const agentStore = useAgentStore()
const { messages, loading, errorMessage, input } = storeToRefs(agentStore)
const { clearMessages, sendMessage, stopTyping } = agentStore

onBeforeRouteLeave(() => {
  stopTyping()
})

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}
</script>

<template>
  <el-card class="chat-page" shadow="never">
    <template #header>
      <el-space direction="vertical" :size="4">
        <el-text tag="h2" size="large">对话</el-text>
        <el-text type="info">向 Agent 提问，测试工具调用、RAG 和普通问答。</el-text>
      </el-space>
    </template>

    <el-scrollbar class="message-scroll">
      <el-space class="message-space" direction="vertical" fill :size="14">
        <article
          v-for="(message, index) in messages"
          :key="index"
          class="message-row"
          :class="message.role"
        >
          <el-card class="message-card" shadow="never">
            <el-text tag="span" type="info" size="small">
              {{ message.role === 'user' ? '你' : 'Agent' }}
            </el-text>
            <p>{{ message.content }}</p>
          </el-card>
        </article>

        <article v-if="loading" class="message-row assistant">
          <el-card class="message-card" shadow="never">
            <el-text tag="span" type="info" size="small">Agent</el-text>
            <p>正在思考...</p>
          </el-card>
        </article>
      </el-space>
    </el-scrollbar>

    <el-alert
      v-if="errorMessage"
      class="error-alert"
      :title="errorMessage"
      type="error"
      show-icon
      :closable="false"
    />

    <el-divider />

    <el-row :gutter="12">
      <el-col :xs="24" :sm="19">
        <el-input
          v-model="input"
          type="textarea"
          :autosize="{ minRows: 3, maxRows: 6 }"
          placeholder="输入问题，例如：对比实验1和实验2的 F1"
          :disabled="loading"
          resize="none"
          @keydown="handleKeydown"
        />
      </el-col>

      <el-col :xs="24" :sm="5">
        <el-space class="composer-actions" direction="vertical" fill>
          <el-button size="large" @click="clearMessages">
            清空
          </el-button>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            :disabled="loading || !input.trim()"
            @click="sendMessage()"
          >
            发送
          </el-button>
        </el-space>
      </el-col>
    </el-row>
  </el-card>
</template>

<style scoped>
.chat-page {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-page :deep(.el-card__body) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.chat-page h2 {
  margin: 0;
}

.message-scroll {
  flex: 1;
  min-height: 0;
}

.message-space {
  width: 100%;
  padding: 4px;
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

.message-card {
  width: min(680px, 82%);
}

.message-row.user .message-card {
  border-color: var(--el-color-primary-light-5);
  background: var(--el-color-primary-light-9);
}

.message-card p {
  margin: 8px 0 0;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.error-alert {
  margin-top: 12px;
}

.composer-actions {
  width: 100%;
}

.composer-actions :deep(.el-button) {
  width: 100%;
  margin-left: 0;
}

@media (max-width: 720px) {
  .message-card {
    width: min(100%, 88%);
  }

  .composer-actions {
    margin-top: 8px;
  }
}
</style>
