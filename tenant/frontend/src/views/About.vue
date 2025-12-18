<template>
  <div class="about">
    <h1>关于租户端</h1>
    <p>这是一个学生SaaS管理系统的租户端，用于管理您的学校或机构。</p>
    <el-button @click="goToHome">返回首页</el-button>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
const goToHome = () => {
  router.push('/')
}
</script>

<style scoped>
.about {
  text-align: center;
  padding: 20px;
}
</style>