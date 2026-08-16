<script setup lang="ts">
import {
  ChatLineRound,
  DataAnalysis,
  List,
} from '@element-plus/icons-vue'
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const activeMenu = computed(() => route.path)
</script>

<template>
  <el-container class="layout-container">
    <el-aside width="220px" class="layout-aside">
      <div class="logo-area">
        <el-text tag="strong" size="large" type="primary">Experiment Agent</el-text>
        <el-text type="info" size="small">Agent Workbench</el-text>
      </div>

      <el-menu
        router
        :default-active="activeMenu"
        class="layout-menu"
      >
        <el-menu-item index="/chat">
          <el-icon>
            <ChatLineRound />
          </el-icon>
          <span>对话</span>
        </el-menu-item>

        <el-menu-item index="/experiments">
          <el-icon>
            <DataAnalysis />
          </el-icon>
          <span>实验管理</span>
        </el-menu-item>

        <el-menu-item index="/activity">
          <el-icon>
            <List />
          </el-icon>
          <span>执行过程</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="layout-header">
        <div>
          <el-text tag="strong">{{ route.meta.title || '对话' }}</el-text>
          <el-text type="info" size="small">
            Agent workflow / RAG / Tool Calling
          </el-text>
        </div>

        <el-tag type="primary" effect="plain" round>
          Day23
        </el-tag>
      </el-header>

      <el-main class="layout-main">
        <router-view v-slot="{ Component }">
          <keep-alive include="ChatView,ExperimentsView,ActivityView">
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout-container {
  height: 100vh;
}

/* 侧边栏深色 */
.layout-aside {
  background: #474849;
  border-right-color: #363637;
}

.logo-area {
  height: 96px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
  padding: 0 20px;
}

/* 菜单在深色背景下的文字和激活色 */
.layout-menu {
  --el-menu-bg-color: #636464;
  --el-menu-text-color: #bfcbd9;
  --el-menu-active-color: #409eff;
  --el-menu-hover-text-color: #fff;
}

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
}

.layout-header > div {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.layout-main {
  height: calc(100vh - 60px);
  padding: 16px;
  overflow: hidden;
  background: var(--el-fill-color-lighter);
}
</style>
