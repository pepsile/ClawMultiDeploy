import request from './request'
import type { ApiResponse, Instance } from '../types'

export const getInstances = () => {
  return request.get<ApiResponse>('/instances')
}

export const createInstance = (id: string, name: string) => {
  return request.post<ApiResponse>('/instances', { id, name })
}

export const deleteInstance = (id: string, keepData: boolean = false) => {
  return request.delete<ApiResponse>(`/instances/${id}?keep_data=${keepData}`)
}

export const startInstance = (id: string) => {
  return request.post<ApiResponse>(`/instances/${id}/start`)
}

export const stopInstance = (id: string) => {
  return request.post<ApiResponse>(`/instances/${id}/stop`)
}

export const initInstance = (id: string) => {
  return request.post<ApiResponse>(`/instances/${id}/init`)
}

export const getInstanceConfig = (id: string) => {
  return request.get<ApiResponse>(`/instances/${id}/config`)
}

export const updateInstanceConfig = (id: string, content: string) => {
  return request.put<ApiResponse>(`/instances/${id}/config`, { content })
}
