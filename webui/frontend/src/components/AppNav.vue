<template>
  <nav class="py-4 px-2">
    <ul class="flex gap-1">
      <li>
        <RouterLink :to="{ name: 'home' }" class="px-4 py-3 hover:bg-zinc-50/10 rounded-2xl transition-colors">
          Library
        </RouterLink>
      </li>
      <li>
        <RouterLink :to="{ name: 'home' }" class="px-4 py-3 hover:bg-zinc-50/10 rounded-2xl transition-colors">
          Catalog
        </RouterLink>
      </li>
      <li>
        <RouterLink :to="{ name: 'home' }" class="px-4 py-3 hover:bg-zinc-50/10 rounded-2xl transition-colors">
          Search
        </RouterLink>
      </li>
    </ul>
  </nav>
</template>
