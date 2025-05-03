<script setup lang="ts">
import type { ButtonHTMLAttributes } from 'vue';

withDefaults(defineProps<{
  type: ButtonHTMLAttributes['type'];
}>(), {
  type: 'button'
});
</script>

<template>
  <button :type class="px-5 py-2.5 text-black font-black rounded-2xl transition-colors">
    <slot />
  </button>
</template>
