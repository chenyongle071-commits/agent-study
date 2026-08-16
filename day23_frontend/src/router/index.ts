import { createRouter, createWebHistory } from 'vue-router'

import ActivityView from '../views/ActivityView.vue'
import ChatView from '../views/ChatView.vue'
import ExperimentsView from '../views/ExperimentsView.vue'
import Layout from '../views/Layout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: Layout as any,
      redirect: '/chat',
      children: [
        {
          path: 'chat',
          component: ChatView as any,
          meta: {
            title: '对话',
          },
        },
        {
          path: 'experiments',
          component: ExperimentsView as any,
          meta: {
            title: '实验管理',
          },
        },
        {
          path: 'activity',
          component: ActivityView as any,
          meta: {
            title: '执行过程',
          },
        },
      ],
    },
  ] as any,
})

export default router
