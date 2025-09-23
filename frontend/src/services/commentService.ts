import { apiClient, ApiResponse } from './api';

export interface Comment {
  id: string;
  block_id: string;
  user_id: string;
  content: string;
  created_at: string;
  updated_at?: string;
  resolved?: boolean;
  user?: {
    id: string;
    full_name: string;
    email: string;
  };
}

export interface CreateCommentRequest {
  block_id: string;
  content: string;
}

export interface CommentListResponse {
  comments: Comment[];
}

export interface CommentResponse {
  comment: Comment;
}

export class CommentService {
  /**
   * Create a new comment
   */
  static async createComment(data: CreateCommentRequest): Promise<ApiResponse<CommentResponse>> {
    return apiClient.post<CommentResponse>('/comment/', data);
  }

  /**
   * Get comments for a block
   */
  static async getCommentsByBlock(blockId: string): Promise<ApiResponse<CommentListResponse>> {
    return apiClient.get<CommentListResponse>(`/comment/?block_id=${blockId}`);
  }

  /**
   * Get comments for a page (all blocks)
   */
  static async getCommentsByPage(pageId: string): Promise<ApiResponse<CommentListResponse>> {
    return apiClient.get<CommentListResponse>(`/comment/?page_id=${pageId}`);
  }

  /**
   * Update comment
   */
  static async updateComment(
    commentId: string, 
    data: { content: string }
  ): Promise<ApiResponse<CommentResponse>> {
    return apiClient.put<CommentResponse>(`/comment/${commentId}`, data);
  }

  /**
   * Delete comment
   */
  static async deleteComment(commentId: string): Promise<ApiResponse<any>> {
    return apiClient.delete(`/comment/${commentId}`);
  }

  /**
   * Resolve comment
   */
  static async resolveComment(commentId: string): Promise<ApiResponse<CommentResponse>> {
    return apiClient.put<CommentResponse>(`/comment/${commentId}/resolve`);
  }

  /**
   * Unresolve comment
   */
  static async unresolveComment(commentId: string): Promise<ApiResponse<CommentResponse>> {
    return apiClient.put<CommentResponse>(`/comment/${commentId}/unresolve`);
  }

  /**
   * Get comment thread
   */
  static async getCommentThread(parentCommentId: string): Promise<ApiResponse<CommentListResponse>> {
    return apiClient.get<CommentListResponse>(`/comment/${parentCommentId}/thread`);
  }

  /**
   * Reply to comment
   */
  static async replyToComment(
    parentCommentId: string, 
    data: { content: string }
  ): Promise<ApiResponse<CommentResponse>> {
    return apiClient.post<CommentResponse>(`/comment/${parentCommentId}/reply`, data);
  }
}