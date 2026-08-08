import { apiClient } from './client';
import { ENDPOINTS } from './endpoints';

export interface FileSearchResult {
  name: string;
  path: string;
  size?: number;
  modified?: string;
  is_directory?: boolean;
}

export const filesService = {
  searchFiles(query: string): Promise<FileSearchResult[]> {
    return apiClient.get<FileSearchResult[]>(ENDPOINTS.FILES.SEARCH, {
      params: { query }
    });
  }
};
export default filesService;
