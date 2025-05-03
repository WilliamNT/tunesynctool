<script setup lang="ts">
import { useAttrs, type ButtonHTMLAttributes } from 'vue';
import AppButtonBase from './AppButtonBase.vue';

const attrs = useAttrs();

withDefaults(defineProps<{
  type: ButtonHTMLAttributes['type'];
  disabled?: boolean;
}>(), {
  type: 'button',
  disabled: false,
});
</script>

<template>
  <AppButtonBase v-bind="attrs" :type="type" :disabled class="bg-lime-400 hover:bg-lime-500" :class="{
    'opacity-45 cursor-not-allowed': disabled,
  }">
    <slot />
  </AppButtonBase>
</template>
