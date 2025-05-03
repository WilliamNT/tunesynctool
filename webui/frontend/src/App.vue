<script setup lang="ts">
import { RouterView } from 'vue-router';
import AppNav from './components/AppNav.vue';
</script>

<template>
  <header>
    <AppNav />
  </header>
  <RouterView />
</template>
