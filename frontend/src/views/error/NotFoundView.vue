<template>
  <main class="not-found">
    <div>
      <span>404</span>
      <h1>页面走丢了</h1>
      <p>你访问的页面不存在，或已被移动。</p>
      <el-button type="primary" @click="$router.push('/dashboard')">返回工作台</el-button>
    </div>
  </main>
</template>

<style scoped>
.not-found {
  display: grid;
  min-height: 100vh;
  place-items: center;
  padding: 24px;
  background: #f5f7fb;
  text-align: center;
}

.not-found span {
  color: #2368df;
  font-size: 88px;
  font-weight: 800;
  letter-spacing: -0.07em;
}

.not-found h1 {
  margin: 8px 0 12px;
}

.not-found p {
  margin-bottom: 24px;
  color: #6d788b;
}
</style>
