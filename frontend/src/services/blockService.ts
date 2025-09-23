import { apiClient, ApiResponse } from './api';

export interface Block {
  id: string;
  page_id: string;
  type: 'paragraph' | 'heading1' | 'heading2' | 'heading3' | 'bulleted-list' | 'numbered-list' | 'todo' | 'quote' | 'code' | 'divider' | 'image';
  content: string;
  created_at: string;
  updated_at?: string;
  order?: number;
  metadata?: any;
}

export interface CreateBlockRequest {
  page_id: string;
  type: Block['type'];
  content: string;
  order?: number;
  metadata?: any;
}

export interface BlockListResponse {
  blocks: Block[];
}

export interface BlockResponse {
  block: Block;
}

export class BlockService {
  /**
   * Create a new block
   */
  static async createBlock(data: CreateBlockRequest): Promise<ApiResponse<BlockResponse>> {
    return apiClient.post<BlockResponse>('/block/', data);
  }

  /**
   * Get list of blocks in a page
   */
  static async getBlocksByPage(pageId: string): Promise<ApiResponse<BlockListResponse>> {
    return apiClient.get<BlockListResponse>(`/block/?page_id=${pageId}`);
  }

  /**
   * Get block by ID
   */
  static async getBlockById(blockId: string): Promise<ApiResponse<BlockResponse>> {
    return apiClient.get<BlockResponse>(`/block/${blockId}`);
  }

  /**
   * Update block content
   */
  static async updateBlock(
    blockId: string, 
    data: Partial<CreateBlockRequest>
  ): Promise<ApiResponse<BlockResponse>> {
    return apiClient.put<BlockResponse>(`/block/${blockId}`, data);
  }

  /**
   * Delete block
   */
  static async deleteBlock(blockId: string): Promise<ApiResponse<any>> {
    return apiClient.delete(`/block/${blockId}`);
  }

  /**
   * Reorder blocks
   */
  static async reorderBlocks(
    pageId: string, 
    blockIds: string[]
  ): Promise<ApiResponse<any>> {
    return apiClient.put(`/block/reorder`, { page_id: pageId, block_ids: blockIds });
  }

  /**
   * Duplicate block
   */
  static async duplicateBlock(blockId: string): Promise<ApiResponse<BlockResponse>> {
    return apiClient.post<BlockResponse>(`/block/${blockId}/duplicate`);
  }

  /**
   * Convert block type
   */
  static async convertBlockType(
    blockId: string, 
    newType: Block['type']
  ): Promise<ApiResponse<BlockResponse>> {
    return apiClient.put<BlockResponse>(`/block/${blockId}/convert`, { type: newType });
  }
}