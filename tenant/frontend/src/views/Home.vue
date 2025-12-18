<template>
  <div class="home">
    <h1>租户端首页</h1>
    <p>欢迎使用学生SaaS管理系统租户端</p>
    <el-button type="primary" @click="goToAbout">关于我们</el-button>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
const goToAbout = () => {
  router.push('/about')
}
</script>

<style scoped>
.home {
  text-align: center;
  padding: 20px;
}
</style>