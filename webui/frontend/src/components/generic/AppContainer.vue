<script setup lang="ts">
withDefaults(defineProps<{
  is?: string;
}>(), {
  is: 'div',
});
</script>

<template>
  <component :is class="w-full" id="main-region">
    <div class="md:w-7xl mx-auto mb-5 flex flex-col h-full">
      <slot />
    </div>
  </component>
</template>
