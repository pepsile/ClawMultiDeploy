import request from './request'
import type { ApiResponse } from '../types'

export const getBackups = () => {
  return request.get<ApiResponse>('/backups')
}

export const createBackup = () => {
  return request.post<ApiResponse>('/backups')
}

export const deleteBackup = (id: number) => {
  return request.delete<ApiResponse>(`/backups/${id}`)
}

export const restoreBackup = (id: number) => {
  return request.post<ApiResponse>(`/backups/${id}/restore`)
}
