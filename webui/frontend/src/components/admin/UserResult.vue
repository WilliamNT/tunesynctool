<script setup lang="ts">
import AppCard from '../card/AppCard.vue';
import { Icon } from '@iconify/vue/dist/iconify.js';
import UserAvatar from '../image/UserAvatar.vue';
import { type UserRead } from '@/api/index.ts';

defineProps<{
  user: UserRead;
}>();
</script>

<template>
  <AppCard class="rounded-2xl flex gap-4 relative overflow-hidden">
    <!-- <button @click="cancelTask" :disabled="isCancellationLoading" class="absolute top-2 right-2 text-zinc-400 w-6 h-6 flex items-center justify-center hover:text-red-200 transition-all z-10 cursor-pointer bg-zinc-400/10 hover:bg-red-100/10 rounded-full" title="Cancel or delete task">
      <Icon icon="svg-spinners:90-ring" v-if="isCancellationLoading" />
      <Icon icon="material-symbols-light:close-small-outline-rounded" class="text-2xl" v-else />
    </button> -->
    <UserAvatar />
    <div class="flex flex-col gap-0.5">
      <h3 class="truncate font-black text-white text-lg m-0 p-0 flex items-center">
        {{ user.username }}
      </h3>
      <ul class="flex gap-2 list-none p-0 m-0 text-sm font-medium text-zinc-400 items-center justify-center">
        <li class="relative pl-3.5 first:pl-0 before:content-['•'] before:absolute before:left-0 first:before:content-[''] before:text-zinc-500 truncate">
          <template v-if="user.is_admin">
            <Icon icon="material-symbols:settings-outline-rounded" class="inline-block me-1 text-lg text-green-200" />
            <span class="text-green-300" title="This user is an administrator.">Admin</span>
          </template>
          <template v-else>
            <Icon icon="material-symbols:account-circle-outline" class="inline-block me-1 text-lg text-blue-200" />
            <span class="text-blue-200">Regular user</span>
          </template>
        </li>
        <li class="relative pl-3.5 first:pl-0 before:content-['•'] before:absolute before:left-0 first:before:content-[''] before:text-zinc-500 truncate">
          User ID: {{ user.id }}
        </li>   
      </ul>
    </div>
  </AppCard>
</template>
