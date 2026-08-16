<script setup lang="ts">
defineOptions({ name: 'ExperimentsView' })

import { computed } from 'vue'

import { mockExperiments } from '../data/experiments'

const experiments = mockExperiments
const maxF1 = 1

const highestF1 = computed(() =>
  experiments.length ? Math.max(...experiments.map((item) => item.f1)) : 0,
)

const lowestLatency = computed(() =>
  experiments.length ? Math.min(...experiments.map((item) => item.latencyMs)) : 0,
)
</script>

<template>
  <el-card class="page-card" shadow="never">
    <template #header>
      <el-space direction="vertical" :size="4">
        <el-text tag="h2" size="large">实验管理</el-text>
        <el-text type="info">
          查看实验列表，并快速比较不同实验的核心指标。
        </el-text>
      </el-space>
    </template>

    <el-space direction="vertical" fill :size="20">
      <el-row :gutter="14">
        <el-col :xs="24" :sm="8">
          <el-card shadow="never">
            <el-statistic title="实验数量" :value="experiments.length" />
          </el-card>
        </el-col>

        <el-col :xs="24" :sm="8">
          <el-card shadow="never">
            <el-statistic title="最高 F1" :value="highestF1" :precision="2" />
          </el-card>
        </el-col>

        <el-col :xs="24" :sm="8">
          <el-card shadow="never">
            <el-statistic title="最低延迟" :value="lowestLatency" suffix=" ms" />
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="never">
        <el-table :data="experiments" border stripe>
          <el-table-column prop="id" label="ID" width="72" />
          <el-table-column prop="name" label="实验名称" min-width="120" />
          <el-table-column prop="modelName" label="模型" min-width="150" />
          <el-table-column prop="datasetName" label="数据集" min-width="140" />

          <el-table-column label="Accuracy" width="110">
            <template #default="{ row }">
              {{ row.accuracy.toFixed(2) }}
            </template>
          </el-table-column>

          <el-table-column label="F1" width="90">
            <template #default="{ row }">
              {{ row.f1.toFixed(2) }}
            </template>
          </el-table-column>

          <el-table-column label="Latency" width="120">
            <template #default="{ row }">
              {{ row.latencyMs }} ms
            </template>
          </el-table-column>

          <el-table-column label="Cost" width="100">
            <template #default="{ row }">
              {{ row.cost.toFixed(2) }}
            </template>
          </el-table-column>

          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <el-tag
                :type="row.status === 'completed' ? 'success' : 'warning'"
                effect="light"
              >
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card shadow="never">
        <template #header>
          <span>F1 指标对比</span>
        </template>

        <div style="display: flex; flex-direction: column; gap: 14px;">
          <div
            v-for="experiment in experiments"
            :key="experiment.id"
            style="display: flex; align-items: center; gap: 12px;"
          >
            <!-- 实验名称，固定宽度右对齐 -->
            <el-text type="info" style="width: 60px; text-align: right; flex-shrink: 0;">
              {{ experiment.name }}：
            </el-text>

            <!-- 进度条，自动撑满剩余空间 -->
            <el-progress
              :percentage="Number(((experiment.f1 / maxF1) * 100).toFixed(0))"
              :format="() => experiment.f1.toFixed(2)"
              style="flex: 1;"
            />

            <!-- 数值文本 -->
            <el-text tag="strong" style="width: 50px; flex-shrink: 0;">
              {{ experiment.f1.toFixed(2) }}
            </el-text>
          </div>
        </div>
      </el-card>
    </el-space>
  </el-card>
</template>

<style scoped>
.page-card {
  height: 100%;
  overflow-y: auto;
}

.page-card h2 {
  margin: 0;
}
</style>
