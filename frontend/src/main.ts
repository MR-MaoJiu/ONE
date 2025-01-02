import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'

// 导入 Font Awesome
import { library } from '@fortawesome/fontawesome-svg-core'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { 
  faComments, 
  faMicrophone, 
  faStop,
  faCog,
  faBrain,
  faTrash,
  faSync,
  faPlus,
  faTimes
} from '@fortawesome/free-solid-svg-icons'

// 添加图标到库
library.add(
  faComments, 
  faMicrophone, 
  faStop, 
  faCog, 
  faBrain,
  faTrash,
  faSync,
  faPlus,
  faTimes
)

// 创建 Pinia 实例
const pinia = createPinia()

// 创建应用实例
const app = createApp(App)

// 使用 Pinia（必须在其他插件之前）
app.use(pinia)

// 注册全局组件和其他插件
app.component('font-awesome-icon', FontAwesomeIcon)
app.use(router)
app.use(ElementPlus)

// 挂载应用
app.mount('#app') 