<script setup lang="ts">
defineOptions({ name: 'ActivityView' })
import { storeToRefs } from 'pinia'

import { useAgentStore } from '../stores/agent'

const agentStore = useAgentStore()
const { activities } = storeToRefs(agentStore)

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
</script>

<template>
  <el-card class="page-card" shadow="never">
    <template #header>
      <el-space direction="vertical" :size="4">
        <el-text tag="h2" size="large">执行过程</el-text>
        <el-text type="info">
          查看最近的 Agent 路由、工具调用结果和引用来源。
        </el-text>
      </el-space>
    </template>

    <el-empty
      v-if="activities.length === 0"
      description="当前还没有执行记录。回到对话发送一个问题后，这里会显示处理过程。"
    />

    <div class="activity-list">
      <el-card
        v-for="(activity, index) in activities"
        :key="`${activity.createdAt}-${index}`"
        shadow="never"
      >
        <template #header>
          <el-row :gutter="16" align="middle" justify="space-between">
            <el-col :span="18">
              <el-space direction="vertical" :size="4">
                <el-text type="info" size="small">
                  {{ activity.createdAt }}
                </el-text>
                <el-text tag="strong">
                  {{ activity.question }}
                </el-text>
              </el-space>
            </el-col>
            <el-col :span="6" class="route-col">
              <el-tag type="primary" effect="light" round>
                {{ activity.route }}
              </el-tag>
            </el-col>
          </el-row>
        </template>

        <el-space direction="vertical" fill :size="16">
          <section>
            <el-text tag="h4">Agent 回答</el-text>
            <p>{{ activity.answer }}</p>
          </section>

          <section>
            <el-text tag="h4">工具结果</el-text>

            <el-descriptions
              v-if="getExperimentDetail(activity.toolResult)"
              border
              :column="3"
            >
              <el-descriptions-item label="调用工具">
                {{ getSelectedTool(activity.toolResult) }}
              </el-descriptions-item>
              <el-descriptions-item label="实验名称">
                {{ getExperimentDetail(activity.toolResult)?.name }}
              </el-descriptions-item>
              <el-descriptions-item label="模型">
                {{ getExperimentDetail(activity.toolResult)?.model_name }}
              </el-descriptions-item>
              <el-descriptions-item label="数据集">
                {{ getExperimentDetail(activity.toolResult)?.dataset_name }}
              </el-descriptions-item>
              <el-descriptions-item label="Accuracy">
                {{ getExperimentDetail(activity.toolResult)?.accuracy }}
              </el-descriptions-item>
              <el-descriptions-item label="F1">
                {{ getExperimentDetail(activity.toolResult)?.f1 }}
              </el-descriptions-item>
              <el-descriptions-item label="Latency">
                {{ getExperimentDetail(activity.toolResult)?.latency_ms }} ms
              </el-descriptions-item>
              <el-descriptions-item label="Cost">
                {{ getExperimentDetail(activity.toolResult)?.cost }}
              </el-descriptions-item>
              <el-descriptions-item label="状态">
                {{ getExperimentDetail(activity.toolResult)?.status }}
              </el-descriptions-item>
            </el-descriptions>

            <pre v-else>{{ JSON.stringify(activity.toolResult, null, 2) }}</pre>
          </section>

          <section>
            <el-text tag="h4">引用来源</el-text>

            <el-empty
              v-if="activity.sources.length === 0"
              description="本次没有返回引用来源。"
              :image-size="72"
            />

            <el-space v-else direction="vertical" fill :size="10">
              <pre
                v-for="(source, sourceIndex) in activity.sources"
                :key="sourceIndex"
                class="source-pre"
              >{{ JSON.stringify(source, null, 2) }}</pre>
            </el-space>
          </section>
        </el-space>
      </el-card>
    </div>  
  </el-card>
</template>

<style scoped>
.source-pre {
  white-space: nowrap;
  overflow-x: auto;
  text-overflow: ellipsis;
}

.page-card {
  height: 100%;
  overflow-y: auto;
}

.page-card h2,
.page-card h4,
.page-card p {
  margin: 0;
}

.page-card p {
  line-height: 1.7;
}

.route-col {
  text-align: right;
}

pre {
  margin: 8px 0 0;
  overflow-x: auto;
  white-space: nowrap; /* 强制单行，超出横向滚动 */
  border-radius: var(--el-border-radius-base);
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-light);
  padding: 10px;
  font-size: 12px;
  line-height: 1.6;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 16px; /* 完美控制上下卡片的间距 */
}
</style>
