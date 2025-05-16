<template>
  <header class="flex flex-col gap-2">
    <h1 class="text-4xl dark:text-white my-5">
      <slot name="title" />
    </h1>
    <p class="text-md font-sembiold text-gray-500 dark:text-gray-400" v-if="$slots.description">
      <slot name="description" />
    </p>
  </header>
</template>
