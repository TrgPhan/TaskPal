import { apiClient, ApiResponse } from './api';

export interface Page {
  id: string;
  workspace_id: string;
  title: string;
  parent_id: string | null;
  created_at: string;
  updated_at?: string;
  is_favorite?: boolean;
  children?: Page[];
}

export interface CreatePageRequest {
  workspace_id: string;
  title: string;
  parent_id?: string | null;
}

export interface PageListResponse {
  pages: Page[];
}

export interface PageResponse {
  page: Page;
}

export class PageService {
  /**
   * Create a new page
   */
  static async createPage(data: CreatePageRequest): Promise<ApiResponse<PageResponse>> {
    return apiClient.post<PageResponse>('/page/', data);
  }

  /**
   * Get list of pages in a workspace
   */
  static async getPagesByWorkspace(workspaceId: string): Promise<ApiResponse<PageListResponse>> {
    return apiClient.get<PageListResponse>(`/page/?workspace_id=${workspaceId}`);
  }

  /**
   * Get page by ID
   */
  static async getPageById(pageId: string): Promise<ApiResponse<PageResponse>> {
    return apiClient.get<PageResponse>(`/page/${pageId}`);
  }

  /**
   * Update page
   */
  static async updatePage(
    pageId: string, 
    data: Partial<CreatePageRequest>
  ): Promise<ApiResponse<PageResponse>> {
    return apiClient.put<PageResponse>(`/page/${pageId}`, data);
  }

  /**
   * Delete page
   */
  static async deletePage(pageId: string): Promise<ApiResponse<any>> {
    return apiClient.delete(`/page/${pageId}`);
  }

  /**
   * Move page to different parent
   */
  static async movePage(
    pageId: string, 
    data: { parent_id: string | null }
  ): Promise<ApiResponse<PageResponse>> {
    return apiClient.put<PageResponse>(`/page/${pageId}/move`, data);
  }

  /**
   * Duplicate page
   */
  static async duplicatePage(pageId: string): Promise<ApiResponse<PageResponse>> {
    return apiClient.post<PageResponse>(`/page/${pageId}/duplicate`);
  }

  /**
   * Toggle page favorite status
   */
  static async toggleFavorite(pageId: string): Promise<ApiResponse<PageResponse>> {
    return apiClient.post<PageResponse>(`/page/${pageId}/favorite`);
  }
}