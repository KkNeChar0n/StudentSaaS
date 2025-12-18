<script setup>
// App component with Element Plus menu and Vue Router
</script>

<template>
  <div id="app">
    <el-menu :router="true" mode="horizontal" default-active="/">
      <el-menu-item index="/">首页</el-menu-item>
      <el-menu-item index="/about">关于</el-menu-item>
    </el-menu>
    <router-view></router-view>
  </div>
</template>

<style scoped>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>