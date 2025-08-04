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

const currentRoute = computed(() => router.currentRoute.value.name);
</script>

<template>
  <nav class="p-3 border-r-1 border-zinc-800 backdrop-blur-2xl sticky top-0 h-screen bg-zinc-900/50 flex flex-col w-64">
    <RouterLink :to="{ name: 'home' }" class="block text-2xl me-4 font-normal">
      tunesynctool
    </RouterLink>
    <hr class="my-3 border-zinc-800" />
    <ul class="flex flex-col gap-2 font-normal" id="nav-items">
      <li>
        <RouterLink :to="{ name: 'home' }" class="flex items-center px-4 py-3 w-full hover:text-lime-400 rounded-full transition-colors">
          <div class="me-2.5 inline-block text-xl">
            <transition name="bounce" mode="out-in">
              <Icon icon="material-symbols:library-music-rounded" :class="{ 'new-page': currentRoute === 'home' }" v-if="currentRoute === 'home'" />
              <Icon icon="material-symbols:library-music-outline-rounded" v-else />
            </transition>
          </div>
          <span>Library</span>
        </RouterLink>
      </li>
      <li>
        <RouterLink :to="{ name: 'search' }" class="flex items-center px-4 py-3 w-full hover:text-lime-400 rounded-full transition-colors">
          <div class="me-2.5 inline-block text-xl">
            <transition name="bounce" mode="out-in">
              <Icon icon="material-symbols:search-rounded" :class="{ 'new-page': currentRoute === 'search' }" v-if="currentRoute === 'search'" />
              <Icon icon="material-symbols:search-rounded" v-else />
            </transition>
          </div>
          <span>Search</span>
        </RouterLink>
      </li>
      <li>
        <RouterLink :to="{ name: 'tasks' }" class="flex items-center px-4 py-3 w-full hover:text-lime-400 rounded-full transition-colors">
          <div class="me-2.5 inline-block text-xl">
            <transition name="bounce" mode="out-in">
              <Icon icon="material-symbols:checklist-rtl-rounded" :class="{ 'new-page': currentRoute === 'tasks' }" v-if="currentRoute === 'tasks'" />
              <Icon icon="material-symbols:checklist-rtl-rounded" v-else />
            </transition>
          </div>
          <span>Tasks</span>
        </RouterLink>
      </li>
      <li>
        <RouterLink :to="{ name: 'accounts' }" class="flex items-center px-4 py-3 w-full hover:text-lime-400 rounded-full transition-colors">
          <div class="me-2.5 inline-block text-xl">
            <transition name="bounce" mode="out-in">
              <Icon icon="material-symbols:settings-rounded" :class="{ 'new-page': currentRoute === 'accounts' }" v-if="currentRoute === 'accounts'" />
              <Icon icon="material-symbols:settings-outline-rounded" v-else />
            </transition>
          </div>
          <span>Accounts</span>
        </RouterLink>
      </li>
    </ul>
  </nav>
</template>

<style scoped>
@keyframes fadeAndBounce {
  0% {
    transform: scale(0.8);
  }

  60% {
    transform: scale(1.05);
  }

  80% {
    transform: scale(0.97);
  }

  100% {
    transform: scale(1);
  }
}

.new-page {
  animation: fadeAndBounce 0.3s ease-out;
}

.bounce-enter-active {
  animation: fadeIn 0.15s ease-out;
}

.bounce-leave-active {
  animation: fadeOut 0.15s ease-in;
}

@keyframes fadeIn {
  0% {
    opacity: 0;
  }

  70% {
    opacity: 1;
  }
}

@keyframes fadeOut {
  0% {
    opacity: 1;
  }

  100% {
    opacity: 0;
  }
}
</style>
