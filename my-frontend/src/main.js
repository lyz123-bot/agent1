import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import './style.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)

app
  .use(createPinia())
  .use(router)
  .use(Antd)
  .mount('#app')
