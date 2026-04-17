<!-- src/views/Login.vue -->
<template>
  <div class="login-container">
    <div class="bg-layer">
      <div class="bg-gradient"></div>
      <div class="bg-glow bg-glow-1"></div>
      <div class="bg-glow bg-glow-2"></div>
      <div class="bg-grid"></div>
    </div>

    <!-- 主内容 -->
    <div class="login-content">
      <!-- ——— 左侧学院介绍 ——— -->
      <div class="login-left">
        <div class="brand-header">
          <div class="logo"><img :src="loginIcon" alt="学院 Logo" /></div>
          <h1>安全科学与应急管理学院</h1>
          <p>大语言模型智能对话系统</p>
        </div>

        <div class="features">
          <div v-for="(f, i) in featureList" :key="i" class="feature">
            <div class="feature-icon"><component :is="f.icon" /></div>
            <div class="feature-text"><h3>{{ f.title }}</h3><p>{{ f.desc }}</p></div>
          </div>
        </div>
      </div>

      <!-- ——— 右侧卡片：根据 isRegister 切换 ——— -->
      <div class="login-right">
        <a-card :title="cardTitle" class="login-card">

          <!-- ************ 登录表单 ************ -->
          <template v-if="!isRegister">
            <a-form :model="form" :rules="rules" @finish="onSubmit"
                    layout="vertical" autocomplete="off">
              <a-form-item name="username" label="用户名">
                <a-input v-model:value="form.username" placeholder="请输入用户名" :disabled="loading">
                  <template #prefix><UserOutlined class="input-icon" /></template>
                </a-input>
              </a-form-item>

              <a-form-item name="password" label="密码">
                <a-input-password v-model:value="form.password" placeholder="请输入密码" :disabled="loading">
                  <template #prefix><LockOutlined class="input-icon" /></template>
                </a-input-password>
              </a-form-item>

              <a-form-item>
                <a-button type="primary" html-type="submit" block :loading="loading" class="submit-btn">
                  <template #default><LoginOutlined class="mr-2" /> 登录</template>
                </a-button>
              </a-form-item>

              <a-row class="switch-link">
                <a href="#" @click.prevent="isRegister = true"><RightOutlined class="link-arrow" /> 没有账号？去注册</a>
              </a-row>
            </a-form>

            <div class="security-tag">
              <SafetyCertificateOutlined /><span>安全科学与应急管理学院认证系统</span>
            </div>
          </template>

          <!-- ************ 注册表单 ************ -->
          <template v-else>
            <!-- 返回按钮 -->
            <div class="back-wrap">
              <a href="#" @click.prevent="isRegister = false"><LeftOutlined class="link-arrow" /> 返回登录</a>
            </div>

            <a-form ref="regForm" :model="reg" :rules="regRules" layout="vertical">
              <a-form-item name="username" label="用户名">
                <a-input v-model:value="reg.username" placeholder="设置用户名">
                  <template #prefix><UserOutlined class="input-icon" /></template>
                </a-input>
              </a-form-item>

              <a-form-item name="email" label="邮箱">
                <a-input v-model:value="reg.email" placeholder="输入邮箱地址">
                  <template #prefix><MailOutlined class="input-icon" /></template>
                </a-input>
              </a-form-item>

              <a-form-item name="password" label="密码">
                <a-input-password v-model:value="reg.password" placeholder="设置密码（至少6位）">
                  <template #prefix><LockOutlined class="input-icon" /></template>
                </a-input-password>
              </a-form-item>

              <a-form-item>
                <a-button type="primary" block :loading="regLoading" @click="onRegister" class="submit-btn">
                  <template #default><UserAddOutlined class="mr-2" /> 注&nbsp;册</template>
                </a-button>
              </a-form-item>
            </a-form>
          </template>
        </a-card>
      </div>
    </div>
  </div>
</template>

<script setup>
/* —— 基础 —— */
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  UserOutlined,
  LockOutlined,
  MailOutlined,
  LoginOutlined,
  UserAddOutlined,
  LeftOutlined,
  RightOutlined,
  SafetyCertificateOutlined,
  BulbOutlined,
  ThunderboltOutlined,
  DatabaseOutlined,
  SafetyOutlined
} from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import loginIcon from '@/assets/login_icon.jpg'

/* —— 环境变量 —— */
const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api'

/* —— 登录相关 —— */
const router    = useRouter()
const userStore = useUserStore()

const form      = ref({ username:'', password:'' })
const loading   = ref(false)
const rules     = {
  username:[{ required:true, message:'请输入用户名', trigger:'blur' }],
  password:[{ required:true, message:'请输入密码', trigger:'blur' }]
}
const cardTitle = computed(()=> isRegister.value ? '创建新账号' : '安全认证登录')

async function onSubmit () {
  loading.value = true
  try {
    const tokRes = await fetch(`${API_BASE}/accounts/token/`,{
      method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(form.value)
    })
    if(!tokRes.ok) throw new Error('登录失败，请检查用户名或密码')
    const { access, refresh } = await tokRes.json()

    const infoRes = await fetch(`${API_BASE}/accounts/me/`,{
      headers:{'Content-Type':'application/json',Authorization:`Bearer ${access}`}
    })
    if(!infoRes.ok) throw new Error('获取用户信息失败')
    const { role } = await infoRes.json()

    userStore.login({ access, refresh, role })
    router.push('/')
    message.success('登录成功')
  } catch(e){ message.error(e.message||'登录出现错误') }
  finally{ loading.value = false }
}

/* —— 注册相关 —— */
const isRegister  = ref(false)                     // ← 关键切换
const reg         = ref({ username:'', email:'', password:'' })
const regRules    = {
  username:[{ required:true, message:'必填', trigger:'blur' }],
  email   :[{ type:'email', message:'邮箱格式不正确', trigger:'blur' }],
  password:[{ required:true, min:6, message:'至少 6 位密码', trigger:'blur' }]
}
const regForm     = ref(null)
const regLoading  = ref(false)
const autoLogin   = false

async function onRegister () {
  try{ await regForm.value.validate() }catch{return}
  regLoading.value = true
  try{
    const r = await fetch(`${API_BASE}/accounts/register/`,{
      method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(reg.value)
    })
    if(!r.ok) throw new Error('注册失败，用户名或邮箱已存在？')
    message.success('注册成功')
    if(autoLogin){ form.value = { ...reg.value }; await onSubmit() }
    isRegister.value = false
  }catch(e){ message.error(e.message) }
  finally{ regLoading.value = false }
}

/* —— 左侧功能列表 —— */
const featureList = [
  { icon: BulbOutlined,       title: '智能风险分析', desc: 'AI驱动的安全风险识别与评估，提供专业决策支持' },
  { icon: ThunderboltOutlined, title: '应急决策支持', desc: '突发事件快速响应，生成科学应急方案' },
  { icon: DatabaseOutlined,    title: '安全知识库',   desc: '整合行业规范、案例库与应急预案的专业知识系统' },
  { icon: SafetyOutlined,     title: '安全认证',     desc: '多重身份验证与数据加密，保障系统安全' }
]
</script>

<style scoped>
.mr-2 { margin-right: 8px; }

.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  padding: 20px;
  color: #fff;
}

/* 背景：与首页一致 */
.bg-layer { position: absolute; inset: 0; z-index: 0; }
.bg-gradient {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 80% 50% at 50% -20%, rgba(22, 119, 255, 0.2), transparent),
    radial-gradient(ellipse 60% 40% at 100% 50%, rgba(88, 28, 135, 0.15), transparent),
    radial-gradient(ellipse 50% 30% at 0% 80%, rgba(6, 182, 212, 0.12), transparent),
    linear-gradient(180deg, #0a0f1a 0%, #0e1628 40%, #0d1424 100%);
}
.bg-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.45;
  animation: float 12s ease-in-out infinite;
}
.bg-glow-1 {
  width: 380px; height: 380px;
  background: rgba(22, 119, 255, 0.25);
  top: -80px; left: 10%;
}
.bg-glow-2 {
  width: 280px; height: 280px;
  background: rgba(88, 28, 135, 0.25);
  bottom: -60px; right: 15%;
  animation-delay: -6s;
}
@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(15px, -20px) scale(1.05); }
}
.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse 80% 80% at 50% 50%, black, transparent);
}

/* 主内容区 */
.login-content {
  display: flex;
  max-width: 1100px;
  width: 100%;
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(16px);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.08);
  z-index: 1;
}

.login-left {
  flex: 1;
  padding: 50px 44px;
  background: linear-gradient(180deg, rgba(13, 19, 32, 0.9) 0%, rgba(10, 15, 26, 0.95) 100%);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.login-right {
  flex: 1;
  padding: 50px 44px;
  background: rgba(13, 19, 32, 0.6);
  display: flex;
  flex-direction: column;
  justify-content: center;
}

/* 左侧品牌与功能 */
.brand-header { text-align: center; margin-bottom: 40px; position: relative; z-index: 1; }
.logo {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  overflow: hidden;
  margin: 0 auto 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid rgba(22, 119, 255, 0.35);
  box-shadow: 0 0 28px rgba(22, 119, 255, 0.25);
}
.logo img { width: 100%; height: 100%; object-fit: cover; }
.brand-header h1 {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 8px;
  background: linear-gradient(135deg, #fff 0%, #a5d8ff 50%, #69b1ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 0.5px;
}
.brand-header p {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.55);
  max-width: 360px;
  margin: 0 auto;
  line-height: 1.6;
}

.features { display: flex; flex-wrap: wrap; gap: 20px; margin-top: 32px; z-index: 1; }
.feature {
  flex: 1 1 calc(50% - 20px);
  min-width: 200px;
  display: flex;
  gap: 14px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.feature:hover {
  border-color: rgba(22, 119, 255, 0.25);
  box-shadow: 0 4px 20px rgba(22, 119, 255, 0.1);
}
.feature-icon {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  background: rgba(22, 119, 255, 0.15);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #69b1ff;
  font-size: 18px;
}
.feature-text h3 { font-size: 15px; margin-bottom: 4px; color: #fff; font-weight: 600; }
.feature-text p { font-size: 13px; color: rgba(255, 255, 255, 0.55); line-height: 1.45; }

/* 登录/注册卡片 */
.login-card {
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
}
:deep(.login-card .ant-card-head) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding: 0 0 24px;
  min-height: auto;
}
:deep(.login-card .ant-card-head-title) {
  color: #fff;
  font-size: 22px;
  font-weight: 600;
  text-align: center;
}
:deep(.login-card .ant-card-body) { padding: 0 0 8px 0; }
:deep(.login-card .ant-form-item-label > label) {
  color: rgba(255, 255, 255, 0.85) !important;
  font-size: 14px;
}
:deep(.login-card .ant-input-affix-wrapper) {
  background: rgba(255, 255, 255, 0.06) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 12px;
  height: 48px;
  padding: 0 16px;
  transition: border-color 0.2s, box-shadow 0.2s;
  cursor: text;
}
:deep(.login-card .ant-input-affix-wrapper .ant-input-prefix) {
  pointer-events: none;
  margin-right: 12px;
}
:deep(.login-card .ant-input-affix-wrapper:hover),
:deep(.login-card .ant-input-affix-wrapper-focused) {
  border-color: rgba(22, 119, 255, 0.45) !important;
  box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.12) !important;
}
:deep(.login-card .ant-input-affix-wrapper input.ant-input) {
  border: none !important;
  background: transparent !important;
  color: #fff !important;
  padding: 12px 0;
  flex: 1;
  min-width: 0;
  position: relative;
  z-index: 1;
}
:deep(.login-card .ant-input::placeholder) {
  color: rgba(255, 255, 255, 0.5) !important;
}
:deep(.login-card .ant-input-password.ant-input-affix-wrapper input.ant-input) {
  color: #fff !important;
  flex: 1;
  min-width: 0;
  position: relative;
  z-index: 1;
}
:deep(.login-card .ant-input-password .ant-input-prefix) {
  pointer-events: none;
  margin-right: 12px;
}
:deep(.login-card .ant-input-password-icon) {
  color: rgba(255, 255, 255, 0.5) !important;
}
.input-icon {
  color: rgba(255, 255, 255, 0.5) !important;
  font-size: 16px;
}
.submit-btn {
  height: 48px !important;
  border-radius: 12px !important;
  font-size: 16px !important;
  font-weight: 500 !important;
  margin-top: 8px !important;
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%) !important;
  border: none !important;
  box-shadow: 0 4px 20px rgba(22, 119, 255, 0.35) !important;
  transition: transform 0.2s, box-shadow 0.2s !important;
}
.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px) !important;
  box-shadow: 0 6px 24px rgba(22, 119, 255, 0.45) !important;
}
.submit-btn:active { transform: translateY(0) !important; }
:deep(.login-card .ant-btn-primary[disabled]) {
  background: rgba(255, 255, 255, 0.1) !important;
  box-shadow: none !important;
}

.switch-link { text-align: right; margin-top: 20px; }
.switch-link a,
.back-wrap a {
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  font-size: 14px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: color 0.2s;
}
.switch-link a:hover,
.back-wrap a:hover {
  color: #69b1ff;
}
.link-arrow { font-size: 12px; }
.back-wrap { margin-bottom: 16px; }

.security-tag {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-top: 28px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;
}

@media (max-width: 900px) {
  .login-content { flex-direction: column; }
  .login-left, .login-right { padding: 40px 28px; }
  .login-left { border-right: none; border-bottom: 1px solid rgba(255, 255, 255, 0.06); }
  .features { margin-top: 24px; }
  .brand-header h1 { font-size: 22px; }
}
@media (max-width: 480px) {
  .feature { flex: 1 1 100%; }
}
</style>
