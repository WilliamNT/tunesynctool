<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(defineProps<{
  is?: string;
  tint?: string;
}>(), {
  is: 'div',
  tint: 'black'
});

const backdropStyling = computed(() => {
  const gradientProperties = [
    `radial-gradient(at 40% 20%, hsla(28, 100%, 74%, .1) 0px, black 100%)`,
    `radial-gradient(at 80% 0%, hsla(189, 100%, 56%, .1) 0px, black 100%)`,
    `radial-gradient(at 0% 50%, hsla(355, 100%, 93%, .1) 0px, black 100%)`,
    `radial-gradient(at 80% 50%, hsla(340, 100%, 76%, .1) 0px, ${props.tint} 100%)`,
    `radial-gradient(at 0% 100%, hsla(22, 100%, 77%, .1) 0px, black 100%)`,
    `radial-gradient(at 80% 100%, hsla(242, 100%, 70%, .1) 0px, black 100%)`,
    `radial-gradient(at 0% 0%, hsla(343, 100%, 76%, .1) 0px, black 100%)`
  ];

  return gradientProperties.join(', ');
});
</script>

<template>
  <component :is class="w-full bg-cover transition-colors duration-500 ease-in-out" :style="{ backgroundImage: backdropStyling }">
    <div class="md:w-6xl mx-auto mb-5 flex flex-col h-full">
      <slot />
    </div>
  </component>
</template>
