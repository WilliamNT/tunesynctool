<script setup lang="ts">
import { useAttrs, type ButtonHTMLAttributes } from 'vue';
import AppButtonBase from './AppButtonBase.vue';

const attrs = useAttrs();

withDefaults(defineProps<{
  type: ButtonHTMLAttributes['type'];
  disabled?: boolean;
  tone?: 'primary' | 'negative';
}>(), {
  type: 'button',
  disabled: false,
  tone: 'primary',
});
</script>

<template>
  <AppButtonBase v-bind="attrs" :type="type" :disabled :class="{
    'opacity-45 cursor-not-allowed': disabled,
    'bg-lime-400 hover:bg-lime-500': tone === 'primary',
    'bg-red-500 hover:bg-red-500/80': tone === 'negative',
  }">
    <slot />
  </AppButtonBase>
</template>
