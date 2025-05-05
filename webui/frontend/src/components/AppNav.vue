<script setup lang="ts">
import { Icon } from '@iconify/vue';
</script>

<template>
  <nav class="py-5 px-2 border-b-1 border-zinc-800 backdrop-blur-2xl sticky top-0 z-10 bg-zinc-900/50 flex items-center">
    <RouterLink :to="{ name: 'home' }" class="block text-2xl me-4">
      tunesynctool
    </RouterLink>
    <ul class="flex gap-1" id="nav-items">
      <li>
        <RouterLink :to="{ name: 'home' }" class="px-4 py-3 hover:text-lime-400 rounded-full transition-colors">
          <Icon icon="material-symbols:library-music-outline-rounded" class="me-2.5 inline-block text-xl"/>Library
        </RouterLink>
      </li>
      <li>
        <RouterLink :to="{ name: 'browse' }" class="px-4 py-3 hover:text-lime-400 rounded-full transition-colors">
          <Icon icon="material-symbols:search-rounded" class="me-2.5 inline-block text-xl"/>Browse
        </RouterLink>
      </li>
      <li>
        <RouterLink :to="{ name: 'tasks' }" class="px-4 py-3 hover:text-lime-400 rounded-full transition-colors">
          <Icon icon="material-symbols:checklist-rtl-rounded" class="me-2.5 inline-block text-xl"/>Tasks
        </RouterLink>
      </li>
      <li>
        <RouterLink :to="{ name: 'accounts' }" class="px-4 py-3 hover:text-lime-400 rounded-full transition-colors">
          <Icon icon="material-symbols:settings-outline-rounded" class="me-2.5 inline-block text-xl"/>Accounts
        </RouterLink>
      </li>
    </ul>
  </nav>
</template>E
