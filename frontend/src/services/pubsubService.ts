import { apiClient, ApiResponse } from './api';
import { io, Socket } from 'socket.io-client';

export interface PubSubMessage {
  channel: string;
  message: string;
  timestamp?: string;
  user_id?: string;
  data?: any;
}

export interface PublishMessageRequest {
  message: string;
  data?: any;
}

export interface PublishResponse {
  channel: string;
  message: string;
}

export class PubSubService {
  private static socket: Socket | null = null;

  /**
   * Initialize Socket.IO connection
   */
  private static initSocket(): Socket | null {
    if (this.socket && this.socket.connected) {
      return this.socket;
    }

    const token = localStorage.getItem('access_token');
    if (!token) {
      console.error('No access token found for Socket.IO connection');
      return null;
    }

    try {
      this.socket = io('http://localhost:8000/ws/pubsub', {
        auth: {
          token: token
        },
        transports: ['websocket'],
        upgrade: false
      });

      this.socket.on('connect', () => {
        console.log('Connected to Socket.IO server');
      });

      this.socket.on('disconnect', () => {
        console.log('Disconnected from Socket.IO server');
      });

      this.socket.on('error', (error) => {
        console.error('Socket.IO error:', error);
      });

      return this.socket;
    } catch (error) {
      console.error('Failed to create Socket.IO connection:', error);
      return null;
    }
  }

  /**
   * Publish message to a channel
   */
  static async publishMessage(
    channel: string, 
    data: PublishMessageRequest
  ): Promise<ApiResponse<PublishResponse>> {
    return apiClient.post<PublishResponse>(`/pubsub/publish/${channel}`, data);
  }

  /**
   * Subscribe to workspace updates
   */
  static subscribeToWorkspace(
    workspaceId: string,
    onMessage: (message: PubSubMessage) => void,
    onError?: (error: any) => void,
    onClose?: () => void
  ): Socket | null {
    const socket = this.initSocket();
    
    if (!socket) return null;

    socket.on('connect', () => {
      console.log('Socket.IO connected, subscribing to workspace:', workspaceId);
      // Subscribe to workspace channel
      socket.emit('subscribe', { channel: `workspace:${workspaceId}` });
    });

    socket.on('subscribed', (data) => {
      console.log('Successfully subscribed to:', data.channel);
    });

    socket.on('message', (data) => {
      try {
        if (data.channel === `workspace:${workspaceId}`) {
          onMessage({
            channel: data.channel,
            message: data.data.message || JSON.stringify(data.data),
            timestamp: data.timestamp,
            user_id: data.data.user_id,
            data: data.data
          });
        }
      } catch (error) {
        console.error('Failed to process Socket.IO message:', error);
        if (onError) onError(error);
      }
    });

    socket.on('error', (error) => {
      console.error('Socket.IO error:', error);
      if (onError) onError(error);
    });

    socket.on('disconnect', () => {
      console.log('Socket.IO connection closed');
      if (onClose) onClose();
    });

    return socket;
  }

  /**
   * Subscribe to page updates
   */
  static subscribeToPage(
    pageId: string,
    onMessage: (message: PubSubMessage) => void,
    onError?: (error: any) => void,
    onClose?: () => void
  ): Socket | null {
    const socket = this.initSocket();
    
    if (!socket) return null;

    socket.on('connect', () => {
      console.log('Socket.IO connected, subscribing to page:', pageId);
      // Subscribe to page channel
      socket.emit('subscribe', { channel: `page:${pageId}` });
    });

    socket.on('subscribed', (data) => {
      console.log('Successfully subscribed to:', data.channel);
    });

    socket.on('message', (data) => {
      try {
        if (data.channel === `page:${pageId}`) {
          onMessage({
            channel: data.channel,
            message: data.data.message || JSON.stringify(data.data),
            timestamp: data.timestamp,
            user_id: data.data.user_id,
            data: data.data
          });
        }
      } catch (error) {
        console.error('Failed to process Socket.IO message:', error);
        if (onError) onError(error);
      }
    });

    socket.on('error', (error) => {
      console.error('Socket.IO error:', error);
      if (onError) onError(error);
    });

    socket.on('disconnect', () => {
      console.log('Socket.IO connection closed');
      if (onClose) onClose();
    });

    return socket;
  }

  /**
   * Disconnect from Socket.IO
   */
  static disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  /**
   * Broadcast typing indicator
   */
  static async broadcastTyping(
    channel: string, 
    data: { user_id: string; is_typing: boolean; block_id?: string }
  ): Promise<ApiResponse<any>> {
    return this.publishMessage(channel, {
      message: 'typing_indicator',
      data
    });
  }

  /**
   * Broadcast cursor position
   */
  static async broadcastCursor(
    channel: string, 
    data: { user_id: string; block_id: string; position: number }
  ): Promise<ApiResponse<any>> {
    return this.publishMessage(channel, {
      message: 'cursor_position',
      data
    });
  }

  /**
   * Broadcast block update
   */
  static async broadcastBlockUpdate(
    channel: string, 
    data: { block_id: string; content: string; user_id: string }
  ): Promise<ApiResponse<any>> {
    return this.publishMessage(channel, {
      message: 'block_updated',
      data
    });
  }

  /**
   * Broadcast user presence
   */
  static async broadcastPresence(
    channel: string, 
    data: { user_id: string; status: 'online' | 'away' | 'offline' }
  ): Promise<ApiResponse<any>> {
    return this.publishMessage(channel, {
      message: 'user_presence',
      data
    });
  }
}