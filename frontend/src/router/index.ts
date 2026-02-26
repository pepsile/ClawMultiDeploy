import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { title: '仪表盘' }
  },
  {
    path: '/instances',
    name: 'Instances',
    component: () => import('../views/Instances.vue'),
    meta: { title: '实例管理' }
  },
  {
    path: '/instances/:id',
    name: 'InstanceDetail',
    component: () => import('../views/InstanceDetail.vue'),
    meta: { title: '实例详情' }
  },
  {
    path: '/backups',
    name: 'Backups',
    component: () => import('../views/Backups.vue'),
    meta: { title: '备份管理' }
  }
]

export default router
