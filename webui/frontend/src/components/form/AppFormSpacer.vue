<script setup lang="ts">
withDefaults(defineProps<{
  direction?: 'row' | 'col';
}>(), {
  direction: 'col'
});
</script>

<template>
  <div class="flex gap-5" :class="{
    'flex-row': direction === 'row',
    'flex-col': direction === 'col'
  }">
    <slot />
  </div>
</template>
