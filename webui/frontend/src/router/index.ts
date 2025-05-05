import { createRouter, createWebHistory } from 'vue-router';

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'home',
            component: () => import('../views/HomeView.vue'),
        },
        {
          path: '/login',
          name: 'login',
          component: () => import('../views/LoginView.vue'),
        },
        {
          path: '/browse',
          name: 'browse',
          component: () => import('../views/BrowseView.vue'),
        },
        {
          path: '/tasks',
          name: 'tasks',
          component: () => import('../views/TasksView.vue'),
        },
        {
          path: '/accounts',
          name: 'accounts',
          component: () => import('../views/AccountsView.vue'),
        }
    ],
});

export default router;
