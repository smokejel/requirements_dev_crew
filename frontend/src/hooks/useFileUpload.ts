import { useState, useCallback } from 'react';
import { useAPI } from './useAPI';
import type { FileUploadResponse } from '../types/apiTypes';

export interface UploadedFile {
  file: File;
  id?: string;
  progress: number;
  uploaded: boolean;
  uploading: boolean;
  error?: string;
  response?: FileUploadResponse;
}

export const useFileUpload = () => {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const { uploadFile, uploadFiles } = useAPI();

  const addFiles = useCallback((newFiles: File[]) => {
    const uploadedFiles: UploadedFile[] = newFiles.map(file => ({
      file,
      progress: 0,
      uploaded: false,
      uploading: false,
    }));
    
    setFiles(prev => [...prev, ...uploadedFiles]);
    return uploadedFiles;
  }, []);

  const removeFile = useCallback((index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  }, []);

  const uploadSingleFile = useCallback(async (index: number) => {
    setFiles(prev => prev.map((f, i) => 
      i === index ? { ...f, uploading: true, progress: 0 } : f
    ));

    try {
      const file = files[index];
      const response = await uploadFile(file.file);
      
      if (response) {
        setFiles(prev => prev.map((f, i) => 
          i === index ? { 
            ...f, 
            uploaded: true, 
            uploading: false, 
            progress: 100,
            id: response.file_id,
            response 
          } : f
        ));
        return response;
      } else {
        throw new Error('Upload failed');
      }
    } catch (error: any) {
      setFiles(prev => prev.map((f, i) => 
        i === index ? { 
          ...f, 
          uploading: false, 
          error: error.message || 'Upload failed' 
        } : f
      ));
      throw error;
    }
  }, [files, uploadFile]);

  const uploadAllFiles = useCallback(async () => {
    const unuploadedFiles = files.filter(f => !f.uploaded && !f.uploading);
    
    if (unuploadedFiles.length === 0) {
      return [];
    }

    // Mark all files as uploading
    setFiles(prev => prev.map(f => 
      !f.uploaded && !f.uploading ? { ...f, uploading: true, progress: 0 } : f
    ));

    try {
      const fileList = unuploadedFiles.map(uf => uf.file);
      const responses = await uploadFiles(fileList);
      
      if (responses) {
        // Update files with responses
        setFiles(prev => prev.map(f => {
          if (!f.uploaded && f.uploading) {
            const responseIndex = unuploadedFiles.findIndex(uf => uf.file === f.file);
            const response = responses[responseIndex];
            
            if (response) {
              return {
                ...f,
                uploaded: true,
                uploading: false,
                progress: 100,
                id: response.file_id,
                response
              };
            }
          }
          return f;
        }));
        
        return responses;
      } else {
        throw new Error('Upload failed');
      }
    } catch (error: any) {
      // Mark all uploading files as failed
      setFiles(prev => prev.map(f => 
        f.uploading ? { 
          ...f, 
          uploading: false, 
          error: error.message || 'Upload failed' 
        } : f
      ));
      throw error;
    }
  }, [files, uploadFiles]);

  const retryUpload = useCallback((index: number) => {
    setFiles(prev => prev.map((f, i) => 
      i === index ? { ...f, error: undefined } : f
    ));
    return uploadSingleFile(index);
  }, [uploadSingleFile]);

  const clearFiles = useCallback(() => {
    setFiles([]);
  }, []);

  const getUploadedFileIds = useCallback(() => {
    return files
      .filter(f => f.uploaded && f.id)
      .map(f => f.id!);
  }, [files]);

  const getUploadedFiles = useCallback(() => {
    return files.filter(f => f.uploaded);
  }, [files]);

  const getFailedFiles = useCallback(() => {
    return files.filter(f => f.error);
  }, [files]);

  const isUploading = useCallback(() => {
    return files.some(f => f.uploading);
  }, [files]);

  const allUploaded = useCallback(() => {
    return files.length > 0 && files.every(f => f.uploaded);
  }, [files]);

  const hasErrors = useCallback(() => {
    return files.some(f => f.error);
  }, [files]);

  return {
    files,
    addFiles,
    removeFile,
    uploadSingleFile,
    uploadAllFiles,
    retryUpload,
    clearFiles,
    getUploadedFileIds,
    getUploadedFiles,
    getFailedFiles,
    isUploading,
    allUploaded,
    hasErrors,
  };
};

export default useFileUpload;