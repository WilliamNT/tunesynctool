<script setup lang="ts">
import { RouterView } from 'vue-router';
import AppNav from './components/AppNav.vue';
</script>

<template>
  <div class="flex">
    <AppNav />
    <RouterView />
  </div>
</template>
