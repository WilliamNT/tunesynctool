<script setup lang="ts">
import { CatalogApi, type PlaylistRead, type PlaylistTaskStatus, type ProviderRead, TaskStatus } from '@/api';
import { computed, onMounted } from 'vue';
import AppCard from '../card/AppCard.vue';
import { ref } from 'vue';
import { get_access_token, get_api_configuration } from '@/services/api';
import { Icon } from '@iconify/vue/dist/iconify.js';
import TaskCover from '../image/TaskCover.vue';
import { intervalToDuration, formatDuration } from 'date-fns';

const props = defineProps<{
  task: PlaylistTaskStatus;
  providers: ProviderRead[];
}>();

const source_provider = computed(() => props.providers.find((p) => p.provider_name === props.task.arguments.from_provider));
const target_provider = computed(() => props.providers.find((p) => p.provider_name === props.task.arguments.to_provider));
const playlist = ref<PlaylistRead>();

const taskDuration = computed(() => {
  const start = new Date(props.task.queued_at * 1000);
  const end = new Date(props.task.done_at ? (props.task.done_at * 1000) : Date.now());
  const duration = intervalToDuration({ start, end });
  const formattedDifference = formatDuration(duration, {
    delimiter: ', '
  });
  return formattedDifference;
});

const config = get_api_configuration(
  get_access_token()
);

const catalogApi = new CatalogApi(config);

onMounted(async () => {
  const playlistResponse = await catalogApi.getPlaylist(props.task.arguments.from_playlist, props.task.arguments.from_provider);
  playlist.value = playlistResponse.data;
});
</script>

<template>
  <AppCard class="rounded-2xl flex gap-4 relative overflow-hidden">
    <TaskCover :provider="source_provider" :track="task.progress.track" :playlist class="my-auto" />
    <div class="flex flex-col gap-0.5">
      <h3 class="truncate font-black text-white text-lg m-0 p-0">{{ playlist?.title ?? 'Loading...' }}</h3>
      <div class="text-xs mb-1 text-zinc-400" v-if="task.progress.track">
        <span class="me-2">{{ task.status === TaskStatus.Running ? 'Current' : 'Last' }}:</span>
        <a :href="task.progress.track.meta.share_url" v-if="task.progress.track.meta.share_url">{{ task.progress.track.title }} - {{ task.progress.track.author.primary }}</a>
        <span v-else>{{ task.progress.track.title }} - {{ task.progress.track.author.primary }}</span>
      </div>
      <div class="text-xs mb-1 text-zinc-400" v-else>No item is being processed.</div>
      <ul class="flex gap-2 list-none p-0 m-0 text-sm font-medium text-zinc-400 items-center justify-center">
        <li class="relative pl-3.5 first:pl-0 before:content-['•'] before:absolute before:left-0 first:before:content-[''] before:text-zinc-500 truncate">
          <template v-if="task.status === TaskStatus.Failed">
            <Icon icon="material-symbols-light:error-outline-rounded" class="inline-block me-1 text-lg text-red-300" />
            <span class="text-red-300">Failed<template v-if="task.status_reason"> - {{ task.status_reason }}</template></span>
          </template>
          <template v-if="task.status === TaskStatus.Finished">
            <Icon icon="material-symbols-light:check-circle-outline" class="inline-block me-1 text-lg text-green-300" />
            <span class="text-green-300">Finished</span>
          </template>
          <template v-if="task.status === TaskStatus.Queued">
            <Icon icon="material-symbols-light:progress-activity" class="animate-spin inline-block me-1 text-lg text-yellow-200" />
            <span class="text-yellow-200">Queued</span>
          </template>
          <template v-if="task.status === TaskStatus.Running">
            <Icon icon="material-symbols-light:directory-sync-rounded" class="animate-spin inline-block me-1 text-lg text-blue-300" />
            <span class="text-blue-300">Running</span>
          </template>
          <template v-if="task.status === TaskStatus.Canceled">
            <Icon icon="material-symbols-light:cancel-outline-rounded" class="inline-block me-1 text-lg text-orange-300" />
            <span class="text-orange-300">Canceled<template v-if="task.status_reason"> - {{ task.status_reason }}</template></span>
          </template>
          <template v-if="task.status === TaskStatus.OnHold">
            <Icon icon="material-symbols-light:directory-sync-rounded" class="animate-spin inline-block me-1 text-lg text-blue-300" />
            <span class="text-blue-300">On hold<template v-if="task.status_reason"> - {{ task.status_reason }}</template></span>
          </template>
        </li>
        <li class="relative pl-3.5 first:pl-0 before:content-['•'] before:absolute before:left-0 first:before:content-[''] before:text-zinc-500 truncate">
          <div class="flex gap-2 items-center text-sm">
            <span>from</span>
            <img :src="source_provider?.ui.favicon" :alt="source_provider?.ui.display_name" class="w-4 h-4" v-if="source_provider" />
            <span>to</span>
            <img :src="target_provider?.ui.favicon" :alt="target_provider?.ui.display_name" class="w-4 h-4" v-if="target_provider" />
          </div>
        </li>
        <li class="relative pl-3.5 first:pl-0 before:content-['•'] before:absolute before:left-0 first:before:content-[''] before:text-zinc-500 truncate">
          {{ task.progress.handled }} items processed<template v-if="task.status === TaskStatus.Running">, {{ task.progress.in_queue }} in queue</template>
        </li>
        <li class="relative pl-3.5 first:pl-0 before:content-['•'] before:absolute before:left-0 first:before:content-[''] before:text-zinc-500 truncate">
          Duration: {{ taskDuration }}
        </li>
        <li class="relative pl-3.5 first:pl-0 before:content-['•'] before:absolute before:left-0 first:before:content-[''] before:text-zinc-500 truncate">
          Playlist ID: {{ task.arguments.from_playlist }}
        </li>
      </ul>
    </div>
    <div class="absolute blur-3xl w-full brightness-150 left-0 top-0  pointer-events-none">
      <img :src="playlist.assets.cover_image" alt="" v-if="playlist?.assets.cover_image" class="object-cover w-full h-full opacity-10 block -bottom-1/2" />
      <div class="bg-white h-full w-1/2 opacity-10" v-else></div>
    </div>
  </AppCard>
</template>
