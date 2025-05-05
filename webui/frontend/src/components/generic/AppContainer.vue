<script setup lang="ts">
withDefaults(defineProps<{
  is?: string;
}>(), {
  is: 'div',
});
</script>

<template>
  <component :is class="max-w-full md:w-6xl mx-auto">
    <slot />
  </component>
</template>
