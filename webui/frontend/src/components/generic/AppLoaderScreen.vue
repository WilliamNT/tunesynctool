<script setup lang="ts">
import { Icon } from '@iconify/vue';
</script>

<template>
  <div class="flex items-center justify-center h-full">
    <div class="flex flex-col items-center gap-4">
      <Icon icon="svg-spinners:3-dots-bounce" class="text-gray-400 text-7xl"/>
      <p class="text-md font-normal text-gray-400 animate-pulse">Loading, please wait...</p>
    </div>
  </div>
</template>
