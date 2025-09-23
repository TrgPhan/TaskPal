import { apiClient, ApiResponse } from './api';

export interface Workspace {
  id: string;
  name: string;
  description: string;
  created_at: string;
  owner_id: string;
  role?: 'owner' | 'admin' | 'member' | 'guest';
  members_count?: number;
  pages_count?: number;
  updated_at?: string;
  is_favorite?: boolean;
}

export interface CreateWorkspaceRequest {
  name: string;
  description: string;
}

export interface WorkspaceListResponse {
  workspaces: Workspace[];
}

export interface WorkspaceResponse {
  workspace: Workspace;
}

export class WorkspaceService {
  /**
   * Create a new workspace
   */
  static async createWorkspace(data: CreateWorkspaceRequest): Promise<ApiResponse<WorkspaceResponse>> {
    return apiClient.post<WorkspaceResponse>('/workspace/', data);
  }

  /**
   * Get list of all workspaces for current user
   */
  static async getWorkspaces(): Promise<ApiResponse<WorkspaceListResponse>> {
    return apiClient.get<WorkspaceListResponse>('/workspace/');
  }

  /**
   * Get workspace by ID
   */
  static async getWorkspaceById(workspaceId: string): Promise<ApiResponse<WorkspaceResponse>> {
    return apiClient.get<WorkspaceResponse>(`/workspace/${workspaceId}`);
  }

  /**
   * Update workspace
   */
  static async updateWorkspace(
    workspaceId: string,
    data: Partial<CreateWorkspaceRequest>
  ): Promise<ApiResponse<WorkspaceResponse>> {
    return apiClient.put<WorkspaceResponse>(`/workspace/${workspaceId}`, data);
  }

  /**
   * Delete workspace
   */
  static async deleteWorkspace(workspaceId: string): Promise<ApiResponse<any>> {
    return apiClient.delete(`/workspace/${workspaceId}`);
  }

  /**
   * Invite member to workspace
   */
  static async inviteMember(
    workspaceId: string,
    data: { email: string; role: string }
  ): Promise<ApiResponse<any>> {
    return apiClient.post(`/workspace/${workspaceId}/members`, data);
  }

  /**
   * Update member role
   */
  static async updateMemberRole(
    workspaceId: string,
    userId: string,
    data: { role: string }
  ): Promise<ApiResponse<any>> {
    return apiClient.put(`/workspace/${workspaceId}/members/${userId}`, data);
  }

  /**
   * Remove member from workspace
   */
  static async removeMember(workspaceId: string, userId: string): Promise<ApiResponse<any>> {
    return apiClient.delete(`/workspace/${workspaceId}/members/${userId}`);
  }

  /**
   * Join workspace by invite code
   */
  static async joinWorkspace(inviteCode: string): Promise<ApiResponse<any>> {
    return apiClient.post(`/workspace/join/${inviteCode}`);
  }

  /**
   * Leave workspace
   */
  static async leaveWorkspace(workspaceId: string): Promise<ApiResponse<any>> {
    return apiClient.post(`/workspace/${workspaceId}/leave`);
  }
}