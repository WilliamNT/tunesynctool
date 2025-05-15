<script setup lang="ts">
import { Icon } from '@iconify/vue';
import { AvatarFallback, AvatarRoot, DropdownMenuContent, DropdownMenuItem, DropdownMenuPortal, DropdownMenuRoot, DropdownMenuTrigger, } from 'reka-ui';
import { delete_access_token, is_access_token_set } from '@/services/api';
import { useRouter } from 'vue-router';
import { computed, toRef } from 'vue';

const router = useRouter();

const handleSignOut = () => {
  delete_access_token();
  router.push({ name: 'login' });
}

const isAuthenticated = computed(() => is_access_token_set());
</script>

<template>
  <nav
    class="py-3 px-5 border-b-1 border-zinc-800 backdrop-blur-2xl sticky top-0 z-10 bg-zinc-900/50 flex items-center">
    <RouterLink :to="{ name: 'home' }" class="block text-2xl me-4">
      tunesynctool
    </RouterLink>
    <ul class="flex gap-1" id="nav-items">
      <li>
        <RouterLink :to="{ name: 'home' }" class="px-4 py-3 hover:text-lime-400 rounded-full transition-colors">
          <Icon icon="material-symbols:library-music-outline-rounded" class="me-2.5 inline-block text-xl" />Library
        </RouterLink>
      </li>
      <li>
        <RouterLink :to="{ name: 'search' }" class="px-4 py-3 hover:text-lime-400 rounded-full transition-colors">
          <Icon icon="material-symbols:search-rounded" class="me-2.5 inline-block text-xl" />Search
        </RouterLink>
      </li>
      <li>
        <RouterLink :to="{ name: 'tasks' }" class="px-4 py-3 hover:text-lime-400 rounded-full transition-colors">
          <Icon icon="material-symbols:checklist-rtl-rounded" class="me-2.5 inline-block text-xl" />Tasks
        </RouterLink>
      </li>
      <li>
        <RouterLink :to="{ name: 'accounts' }" class="px-4 py-3 hover:text-lime-400 rounded-full transition-colors">
          <Icon icon="material-symbols:settings-outline-rounded" class="me-2.5 inline-block text-xl" />Accounts
        </RouterLink>
      </li>
    </ul>
    <DropdownMenuRoot v-if="isAuthenticated">
      <DropdownMenuTrigger aria-label="Account options" class="ms-auto">
        <AvatarRoot class="flex items-center justify-center w-12 h-12 p-2 rounded-full bg-zinc-600/40 ring-1 ring-zinc-700 cursor-pointer">
          <AvatarFallback class="text-zinc-200 leading-1 flex h-full w-full items-center justify-center text-sm font-black">
            <Icon icon="material-symbols:person-outline-rounded" class="text-2xl" />
          </AvatarFallback>
        </AvatarRoot>
      </DropdownMenuTrigger>
      <DropdownMenuPortal>
        <DropdownMenuContent side="bottom" :side-offset="5" align="end" class="bg-zinc-800 border border-zinc-700 rounded-xl shadow-lg overflow-hidden z-10 mt-2 min-w-[200px] p-1.5" >
          <DropdownMenuItem value="Sign Out" @click="handleSignOut">
            <div class="flex gap-2 items-center hover:bg-zinc-700/50 cursor-pointer transition-all rounded-lg p-2">
              <Icon icon="material-symbols:logout-rounded" />
              <span class="truncate text-md text-zinc-300/90">
                Sign Out
              </span>
            </div>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenuPortal>
    </DropdownMenuRoot>
  </nav>
</template>
