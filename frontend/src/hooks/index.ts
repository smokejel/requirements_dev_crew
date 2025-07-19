// Export all hooks from a single entry point
export { useAPI, default as useAPIHook } from './useAPI';
export { useWebSocket, default as useWebSocketHook } from './useWebSocket';
export { useFileUpload, default as useFileUploadHook } from './useFileUpload';
export type { UploadedFile } from './useFileUpload';