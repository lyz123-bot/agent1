<template>
  <div class="home">
    <!-- 背景层：渐变 + 动态光晕 -->
    <div class="bg-layer">
      <div class="bg-gradient"></div>
      <div class="bg-glow bg-glow-1"></div>
      <div class="bg-glow bg-glow-2"></div>
      <div class="bg-glow bg-glow-3"></div>
      <div class="bg-grid"></div>
    </div>

    <!-- 主内容 -->
    <main class="content">
      <header class="hero">
        <h1 class="hero-title">
          <span class="hero-title-text">安应 Agent</span>
        </h1>
        <p class="hero-desc">智能对话 · 识图定位 · 向量检索，一站式 AI 工作台</p>
      </header>

      <nav class="cards">
        <a
          v-for="item in modules"
          :key="item.path"
          :href="item.path"
          class="card"
          @click.prevent="goTo(item.path)"
        >
          <span class="card-glow"></span>
          <span class="card-icon" :class="item.iconClass">{{ item.icon }}</span>
          <h3 class="card-title">{{ item.label }}</h3>
          <p class="card-desc">{{ item.desc }}</p>
          <span class="card-arrow">→</span>
        </a>
      </nav>

      <footer class="footer">
        <span class="footer-dot"></span>
        <span>已就绪，选择上方模块开始使用</span>
      </footer>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const user = useUserStore()

const baseModules = [
  { path: '/chat', label: '智能对话', desc: '多轮对话与流式回复', icon: '💬', iconClass: 'icon-chat' },
  { path: '/locator', label: '智能识图', desc: '图像识别与定位', icon: '🧭', iconClass: 'icon-locator' }
]

const modules = computed(() =>
  user.isAdmin
    ? [
        ...baseModules,
        { path: '/vdb', label: '向量数据库', desc: '知识库构建与检索', icon: '📦', iconClass: 'icon-vdb' }
      ]
    : baseModules
)

function goTo(path) {
  router.push(path)
}
</script>

<style scoped>
.home {
  position: relative;
  min-height: 100%;
  width: 100%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ─── 背景 ─── */
.bg-layer {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.bg-gradient {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 80% 50% at 50% -20%, rgba(22, 119, 255, 0.25), transparent),
    radial-gradient(ellipse 60% 40% at 100% 50%, rgba(88, 28, 135, 0.2), transparent),
    radial-gradient(ellipse 50% 30% at 0% 80%, rgba(6, 182, 212, 0.15), transparent),
    linear-gradient(180deg, #0a0f1a 0%, #0e1628 40%, #0d1424 100%);
}

.bg-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.5;
  animation: float 12s ease-in-out infinite;
}

.bg-glow-1 {
  width: 400px;
  height: 400px;
  background: rgba(22, 119, 255, 0.25);
  top: -100px;
  left: 10%;
  animation-delay: 0s;
}

.bg-glow-2 {
  width: 300px;
  height: 300px;
  background: rgba(88, 28, 135, 0.3);
  top: 40%;
  right: -50px;
  animation-delay: -4s;
}

.bg-glow-3 {
  width: 250px;
  height: 250px;
  background: rgba(6, 182, 212, 0.2);
  bottom: -50px;
  left: 30%;
  animation-delay: -8s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(20px, -30px) scale(1.05); }
  66% { transform: translate(-15px, 20px) scale(0.95); }
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse 70% 70% at 50% 50%, black, transparent);
}

/* ─── 内容 ─── */
.content {
  position: relative;
  z-index: 1;
  padding: 48px 24px;
  max-width: 920px;
  width: 100%;
  text-align: center;
}

.hero {
  margin-bottom: 48px;
}

.hero-title {
  margin: 0 0 12px;
  font-size: clamp(2rem, 5vw, 3rem);
  font-weight: 700;
  letter-spacing: -0.02em;
}

.hero-title-text {
  background: linear-gradient(135deg, #fff 0%, #a5d8ff 50%, #69b1ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: titleShine 4s ease-in-out infinite;
}

@keyframes titleShine {
  0%, 100% { filter: brightness(1); }
  50% { filter: brightness(1.15); }
}

.hero-desc {
  margin: 0;
  color: rgba(255, 255, 255, 0.55);
  font-size: 1rem;
  letter-spacing: 0.08em;
}

/* ─── 卡片 ─── */
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 20px;
  justify-content: center;
  margin-bottom: 40px;
}

.card {
  position: relative;
  display: block;
  padding: 28px 24px;
  text-align: left;
  text-decoration: none;
  color: inherit;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  overflow: hidden;
  transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
  cursor: pointer;
}

.card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(22, 119, 255, 0.08) 0%, transparent 50%);
  opacity: 0;
  transition: opacity 0.25s ease;
  pointer-events: none;
}

.card:hover {
  transform: translateY(-4px);
  border-color: rgba(22, 119, 255, 0.35);
  box-shadow: 0 20px 40px -12px rgba(0, 0, 0, 0.4);
}

.card:hover::before {
  opacity: 1;
}

.card-glow {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle at 50% 50%, rgba(22, 119, 255, 0.12) 0%, transparent 50%);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.card:hover .card-glow {
  opacity: 1;
}

.card-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  margin-bottom: 16px;
  font-size: 1.5rem;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  transition: background 0.25s ease, transform 0.25s ease;
}

.card:hover .card-icon {
  background: rgba(22, 119, 255, 0.2);
  transform: scale(1.05);
}

.card-title {
  margin: 0 0 6px;
  font-size: 1.15rem;
  font-weight: 600;
  color: #fff;
}

.card-desc {
  margin: 0 0 12px;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.5);
  line-height: 1.4;
}

.card-arrow {
  display: inline-block;
  font-size: 1.25rem;
  color: rgba(22, 119, 255, 0.9);
  transition: transform 0.25s ease;
}

.card:hover .card-arrow {
  transform: translateX(4px);
}

/* ─── 页脚 ─── */
.footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.35);
}

.footer-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #52c41a;
  box-shadow: 0 0 10px #52c41a;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.1); }
}
</style>
