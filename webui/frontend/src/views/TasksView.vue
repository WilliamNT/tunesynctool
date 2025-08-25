<!-- eslint-disable vue/no-use-v-if-with-v-for -->
<script setup lang="ts">
import { get_access_token, get_api_configuration } from '@/services/api';
import { ProvidersApi, TasksApi, TaskStatus, type PlaylistTaskStatus, type ProviderRead } from '@/api';
import { computed, onMounted, onUnmounted, ref } from 'vue';
import AppContainer from '@/components/generic/AppContainer.vue';
import AppLoaderScreen from '@/components/generic/AppLoaderScreen.vue';
import AppPageHeader from '@/components/generic/AppPageHeader.vue';
import Task from '@/components/library/Task.vue';
import PlaylistTaskForm from '@/components/service/PlaylistTaskForm.vue';
import AppCard from '@/components/card/AppCard.vue';

const config = get_api_configuration(
  get_access_token()
);

const tasksApi = new TasksApi(config);
const providersApi = new ProvidersApi(config);

const isLoading = ref(true);

const providers = ref<ProviderRead[]>([]);
const tasks = ref<PlaylistTaskStatus[]>([]);
let intervalId: number | undefined = undefined;

const historyTasks = computed(() => {
  return tasks.value.filter(task => task.status !== TaskStatus.Running && task.status !== TaskStatus.OnHold && task.status !== TaskStatus.Queued);
});

const runningTasks = computed(() => {
  return tasks.value.filter(task => task.status === TaskStatus.Running || task.status === TaskStatus.OnHold);
});

const queuedTasks = computed(() => {
  return tasks.value.filter(task => task.status === TaskStatus.Queued);
});

const fetchTasks = async () => {
  const tasksResponse = await tasksApi.getTasks();
  tasks.value = tasksResponse.data.items ?? [];
}

const startPolling = () => {
  intervalId = setTimeout(async () => {
      if (document.visibilityState === 'visible') {
        await fetchTasks();
      }

      startPolling();
  }, 3000);
}

onMounted(async () => {
  isLoading.value = true;

  await fetchTasks();

  const providersResponse = await providersApi.getValidProviderNames();
  providers.value = providersResponse.data.items ?? [];

  isLoading.value = false;

  startPolling();
});

onUnmounted(() => {
  clearTimeout(intervalId);
});
</script>

<template>
  <AppContainer is="main">
    <AppLoaderScreen v-if="isLoading" />
    <template v-else>
      <AppPageHeader>
        <template #title>
          Tasks
        </template>
        <template #description>
          Review tasks you previously initiated and start new ones.
        </template>
      </AppPageHeader>
      <div class="flex flex-col gap-3 mt-8">
        <AppCard>
          <PlaylistTaskForm :providers />
        </AppCard>
        <div class="flex items-center gap-3 w-full mb-3 mt-8">
          <h2 class="text-2xl">Running now</h2>
          <hr class="flex-1 border-zinc-700 border-0.5 ms-5" />
        </div>
        <Task :providers :task v-for="task in runningTasks" :key="task.task_id" v-if="runningTasks.length > 0" />
        <p class="text-sm text-zinc-400 font-normal" v-else>You have no running tasks.</p>
      </div>
      <div class="flex flex-col gap-3 mt-8">
        <div class="flex items-center gap-3 w-full mb-3">
          <h2 class="text-2xl">In queue</h2>
          <hr class="flex-1 border-zinc-700 border-0.5 ms-5" />
        </div>
        <Task :providers :task v-for="task in queuedTasks" :key="task.task_id" v-if="queuedTasks.length > 0" />
        <p class="text-sm text-zinc-400 font-normal" v-else>You have no tasks waiting in queue.</p>
      </div>
      <div class="flex flex-col gap-3 mt-8">
        <div class="flex items-center gap-3 w-full mb-3">
          <h2 class="text-2xl">History</h2>
          <hr class="flex-1 border-zinc-700 border-0.5 ms-5" />
        </div>
        <Task :providers :task v-for="task in historyTasks" :key="task.task_id" v-if="historyTasks.length > 0" />
        <p class="text-sm text-zinc-400 font-normal" v-else>You don't have any finished tasks yet.</p>
      </div>
    </template>
  </AppContainer>
</template>
