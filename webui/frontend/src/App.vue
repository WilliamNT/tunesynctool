<script setup lang="ts">
import { RouterView } from 'vue-router';
import AppNav from './components/AppNav.vue';
import { isAuthenticated } from './services/api';
</script>

<template>
  <div class="flex flex-1">
    <AppNav v-if="isAuthenticated" />
    <RouterView />
  </div>
</template>
