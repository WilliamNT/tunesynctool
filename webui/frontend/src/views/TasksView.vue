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
import AppNotification from '@/components/generic/AppNotification.vue';

const config = get_api_configuration(
  get_access_token()
);

const tasksApi = new TasksApi(config);
const providersApi = new ProvidersApi(config);

const isLoading = ref(true);

const providers = ref<ProviderRead[]>([]);
const tasks = ref<PlaylistTaskStatus[]>([]);
const notificationOpen = ref(false);
const notificationKey = ref(0);
const submittedTask = ref<PlaylistTaskStatus>();
let intervalId: ReturnType<typeof setTimeout> | undefined = undefined;

const providerDisplayNameByName = computed(() => {
  return new Map(providers.value.map(provider => [
    provider.provider_name,
    provider.ui.display_name,
  ]));
});

function shouldEntryBeHiddenForProviderUnavailability(task: PlaylistTaskStatus): boolean {
  const fromProvider = providers.value.find(p => p.provider_name === task.arguments.from_provider);
  const toProvider = providers.value.find(p => p.provider_name === task.arguments.to_provider);

  if (!fromProvider || !toProvider) {
    return true;
  }

  return !(fromProvider.is_configured && fromProvider.linking.linked) || !(toProvider.is_configured && toProvider.linking.linked);
}

const historyTasks = computed(() => {
  return tasks.value.filter(task => task.status !== TaskStatus.Running && task.status !== TaskStatus.OnHold && task.status !== TaskStatus.Queued);
});

const visibleHistoryTasks = computed(() => {
  return historyTasks.value.filter(task => !shouldEntryBeHiddenForProviderUnavailability(task));
});

const hiddenHistoryTasksCount = computed(() => {
  return historyTasks.value.filter(task => shouldEntryBeHiddenForProviderUnavailability(task)).length;
});

const runningTasks = computed(() => {
  return tasks.value.filter(task => task.status === TaskStatus.Running || task.status === TaskStatus.OnHold);
});

const visibleRunningTasks = computed(() => {
  return runningTasks.value.filter(task => !shouldEntryBeHiddenForProviderUnavailability(task));
});

const hiddenRunningTasksCount = computed(() => {
  return runningTasks.value.filter(task => shouldEntryBeHiddenForProviderUnavailability(task)).length;
});

const queuedTasks = computed(() => {
  return tasks.value.filter(task => task.status === TaskStatus.Queued);
});

const visibleQueuedTasks = computed(() => {
  return queuedTasks.value.filter(task => !shouldEntryBeHiddenForProviderUnavailability(task));
});

const hiddenQueuedTasksCount = computed(() => {
  return queuedTasks.value.filter(task => shouldEntryBeHiddenForProviderUnavailability(task)).length;
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

const handleTaskSubmitted = async (task: PlaylistTaskStatus) => {
  submittedTask.value = task;
  notificationKey.value += 1;
  notificationOpen.value = true;
  await fetchTasks();
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
          <PlaylistTaskForm :providers @submitted="handleTaskSubmitted" />
        </AppCard>
        <div class="flex items-center gap-3 w-full mb-3 mt-8">
          <h2 class="text-2xl">Running now</h2>
          <p class="text-sm text-zinc-400 font-normal" v-if="hiddenRunningTasksCount > 0">({{ hiddenRunningTasksCount }} hidden)</p>
          <hr class="flex-1 border-zinc-700 border-0.5 ms-5" />
        </div>
        <template v-if="visibleRunningTasks.length > 0">
          <Task v-for="task in visibleRunningTasks" :key="task.task_id" :providers :task @cancel="fetchTasks" />
        </template>
        <p class="text-sm text-zinc-400 font-normal" v-else>You have no running tasks.</p>
      </div>
      <div class="flex flex-col gap-3 mt-8">
        <div class="flex items-center gap-3 w-full mb-3">
          <h2 class="text-2xl">In queue</h2>
          <div class="text-sm text-zinc-400 font-normal" v-if="hiddenQueuedTasksCount > 0">({{ hiddenQueuedTasksCount }} hidden)</div>
          <hr class="flex-1 border-zinc-700 border-0.5 ms-5" />
        </div>
        <template v-if="visibleQueuedTasks.length > 0">
          <Task v-for="task in visibleQueuedTasks" :key="task.task_id" :providers :task />
        </template>
        <p class="text-sm text-zinc-400 font-normal" v-else>You have no tasks waiting in queue.</p>
      </div>
      <div class="flex flex-col gap-3 mt-8">
        <div class="flex items-center gap-3 w-full mb-3">
          <h2 class="text-2xl">History</h2>
          <div class="text-xs text-zinc-400 font-normal" v-if="hiddenHistoryTasksCount > 0">({{ hiddenHistoryTasksCount }} hidden)</div>
          <hr class="flex-1 border-zinc-700 border-0.5 ms-5" />
        </div>
        <template v-if="visibleHistoryTasks.length > 0">
          <Task v-for="task in visibleHistoryTasks" :key="task.task_id" :providers :task />
        </template>
        <p class="text-sm text-zinc-400 font-normal" v-else>You don't have any finished tasks yet.</p>
      </div>
    </template>
    <AppNotification
      v-if="submittedTask"
      :key="notificationKey"
      v-model:open="notificationOpen"
      title="Transfer queued"
      icon="material-symbols:checklist-rtl-rounded"
      :duration="3500"
    >
      <span>
        Transfering playlist from
        <strong>{{ providerDisplayNameByName.get(submittedTask.arguments.from_provider) ?? submittedTask.arguments.from_provider }}</strong>
        to
        <strong>{{ providerDisplayNameByName.get(submittedTask.arguments.to_provider) ?? submittedTask.arguments.to_provider }}</strong>.
      </span>
    </AppNotification>
  </AppContainer>
</template>
