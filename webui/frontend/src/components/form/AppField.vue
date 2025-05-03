<script setup lang="ts">
import type { InputHTMLAttributes } from 'vue';
import { useAttrs } from 'vue';

const model = defineModel();

defineProps<{
  name: string;
  label?: string;
  hint?: string;
  error?: string;
}>();

const attrs = useAttrs();

const emit = defineEmits(['update:modelValue', 'blur']);
</script>

<template>
  <div class="flex flex-col gap-1 max-w-md">
    <label :for="name" v-if="label" class="font-bold pb-1 capitalize">
      {{ label }}
    </label>
    <input v-bind="attrs" @blur="$emit('blur')" v-model="model" :id="name" :name class="bg-zinc-800 px-3 py-2 rounded-xl border-1 focus:outline-0 transition-colors font-medium placeholder:text-zinc-300/30" :class="{
      'border-zinc-700 focus:border-lime-500': !error,
      'border-red-400 focus:border-red-400': error
    }">
    <span v-if="error" class="text-red-400 font-normal text-sm">{{ error }}</span>
    <span v-if="hint" class="text-zinc-400 font-normal text-sm">{{ hint }}</span>
  </div>
</template>
