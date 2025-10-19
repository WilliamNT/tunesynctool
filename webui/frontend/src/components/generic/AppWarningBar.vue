<script setup lang="ts">
defineProps<{
    message: string
}>()
</script>

<template>
    <div class="w-fit py-3 px-5 mx-auto mt-5 bg-gradient-to-b from-yellow-300 to-yellow-400 rounded-xl shadow-xl">
        <p class="text-black text-center text-sm">{{ message }}</p>
    </div>
</template>
