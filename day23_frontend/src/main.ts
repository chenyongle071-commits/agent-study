import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { createPinia } from 'pinia'
import 'element-plus/dist/index.css'

import App from './App.vue'
import './assets/main.css'
import router from './router'

const app = createApp(App)
const pinia = createPinia()

app.use(ElementPlus, { locale: zhCn })
app.use(pinia)
app.use(router as never)
app.mount('#app')
