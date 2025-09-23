import React, { createContext, useContext, useState, useEffect } from 'react';
import { BlockService, Block } from '../services/blockService';
import { CommentService, Comment } from '../services/commentService';
import { PubSubService, PubSubMessage } from '../services/pubsubService';
import { PageService, Page } from '../services/pageService';
import { toast } from 'sonner';

interface PageEditorContextType {
  currentPage: Page | null;
  blocks: Block[];
  comments: Comment[];
  loading: boolean;
  saving: boolean;
  wsConnection: WebSocket | null;
  activeUsers: any[];
  
  // Page operations
  loadPage: (pageId: string) => Promise<void>;
  updatePageTitle: (pageId: string, title: string) => Promise<void>;
  
  // Block operations
  createBlock: (data: { page_id: string; type: Block['type']; content: string; afterBlockId?: string }) => Promise<Block | null>;
  updateBlock: (blockId: string, content: string) => Promise<void>;
  deleteBlock: (blockId: string) => Promise<void>;
  reorderBlocks: (blockIds: string[]) => Promise<void>;
  convertBlockType: (blockId: string, newType: Block['type']) => Promise<void>;
  
  // Comment operations
  createComment: (blockId: string, content: string) => Promise<Comment | null>;
  updateComment: (commentId: string, content: string) => Promise<void>;
  deleteComment: (commentId: string) => Promise<void>;
  resolveComment: (commentId: string) => Promise<void>;
  
  // Real-time features
  connectToPage: (pageId: string) => void;
  disconnectFromPage: () => void;
  broadcastTyping: (blockId: string, isTyping: boolean) => void;
  broadcastCursorPosition: (blockId: string, position: number) => void;
}

const PageEditorContext = createContext<PageEditorContextType | undefined>(undefined);

export function PageEditorProvider({ children }: { children: React.ReactNode }) {
  const [currentPage, setCurrentPage] = useState<Page | null>(null);
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);
  const [activeUsers, setActiveUsers] = useState<any[]>([]);

  // Load page and its content
  const loadPage = async (pageId: string) => {
    setLoading(true);
    try {
      // Load page details
      const pageResponse = await PageService.getPageById(pageId);
      if (pageResponse.success && pageResponse.data) {
        setCurrentPage(pageResponse.data.page);
      }

      // Load blocks
      const blocksResponse = await BlockService.getBlocksByPage(pageId);
      if (blocksResponse.success && blocksResponse.data) {
        setBlocks(blocksResponse.data.blocks.sort((a, b) => (a.order || 0) - (b.order || 0)));
      }

      // Load comments
      const commentsResponse = await CommentService.getCommentsByPage(pageId);
      if (commentsResponse.success && commentsResponse.data) {
        setComments(commentsResponse.data.comments);
      }

      // Connect to real-time updates
      connectToPage(pageId);
    } catch (error: any) {
      toast.error(error.message || 'Failed to load page');
    } finally {
      setLoading(false);
    }
  };

  // Update page title
  const updatePageTitle = async (pageId: string, title: string) => {
    setSaving(true);
    try {
      const response = await PageService.updatePage(pageId, { title });
      if (response.success && response.data) {
        setCurrentPage(response.data.page);
        toast.success('Page title updated');
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to update page title');
    } finally {
      setSaving(false);
    }
  };

  // Create new block
  const createBlock = async (data: { 
    page_id: string; 
    type: Block['type']; 
    content: string; 
    afterBlockId?: string 
  }): Promise<Block | null> => {
    try {
      // Calculate order based on position
      let order = blocks.length;
      if (data.afterBlockId) {
        const afterBlock = blocks.find(b => b.id === data.afterBlockId);
        if (afterBlock) {
          order = (afterBlock.order || 0) + 1;
        }
      }

      const response = await BlockService.createBlock({
        page_id: data.page_id,
        type: data.type,
        content: data.content,
        order
      });

      if (response.success && response.data) {
        const newBlock = response.data.block;
        
        if (data.afterBlockId) {
          const afterIndex = blocks.findIndex(b => b.id === data.afterBlockId);
          const newBlocks = [...blocks];
          newBlocks.splice(afterIndex + 1, 0, newBlock);
          setBlocks(newBlocks);
        } else {
          setBlocks(prev => [...prev, newBlock]);
        }

        // Broadcast block creation
        if (wsConnection && currentPage) {
          await PubSubService.broadcastBlockUpdate(`page_${currentPage.id}`, {
            block_id: newBlock.id,
            content: newBlock.content,
            user_id: 'current_user' // TODO: Get from auth context
          });
        }

        return newBlock;
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to create block');
    }
    return null;
  };

  // Update block content
  const updateBlock = async (blockId: string, content: string) => {
    try {
      // Optimistically update UI
      setBlocks(prev => prev.map(block => 
        block.id === blockId ? { ...block, content } : block
      ));

      const response = await BlockService.updateBlock(blockId, { content });
      
      if (response.success) {
        // Broadcast block update
        if (wsConnection && currentPage) {
          await PubSubService.broadcastBlockUpdate(`page_${currentPage.id}`, {
            block_id: blockId,
            content,
            user_id: 'current_user' // TODO: Get from auth context
          });
        }
      } else {
        // Revert on failure
        const originalBlock = blocks.find(b => b.id === blockId);
        if (originalBlock) {
          setBlocks(prev => prev.map(block => 
            block.id === blockId ? originalBlock : block
          ));
        }
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to update block');
      // Revert changes
      const originalBlock = blocks.find(b => b.id === blockId);
      if (originalBlock) {
        setBlocks(prev => prev.map(block => 
          block.id === blockId ? originalBlock : block
        ));
      }
    }
  };

  // Delete block
  const deleteBlock = async (blockId: string) => {
    try {
      const response = await BlockService.deleteBlock(blockId);
      if (response.success) {
        setBlocks(prev => prev.filter(block => block.id !== blockId));
        toast.success('Block deleted');
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to delete block');
    }
  };

  // Reorder blocks
  const reorderBlocks = async (blockIds: string[]) => {
    if (!currentPage) return;

    try {
      // Optimistically update UI
      const reorderedBlocks = blockIds.map(id => blocks.find(b => b.id === id)!).filter(Boolean);
      setBlocks(reorderedBlocks);

      const response = await BlockService.reorderBlocks(currentPage.id, blockIds);
      if (!response.success) {
        // Revert on failure
        setBlocks(blocks);
        toast.error('Failed to reorder blocks');
      }
    } catch (error: any) {
      // Revert on error
      setBlocks(blocks);
      toast.error(error.message || 'Failed to reorder blocks');
    }
  };

  // Convert block type
  const convertBlockType = async (blockId: string, newType: Block['type']) => {
    try {
      const response = await BlockService.convertBlockType(blockId, newType);
      if (response.success && response.data) {
        setBlocks(prev => prev.map(block => 
          block.id === blockId ? response.data!.block : block
        ));
        toast.success('Block type changed');
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to convert block type');
    }
  };

  // Create comment
  const createComment = async (blockId: string, content: string): Promise<Comment | null> => {
    try {
      const response = await CommentService.createComment({ block_id: blockId, content });
      if (response.success && response.data) {
        const newComment = response.data.comment;
        setComments(prev => [...prev, newComment]);
        toast.success('Comment added');
        return newComment;
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to add comment');
    }
    return null;
  };

  // Update comment
  const updateComment = async (commentId: string, content: string) => {
    try {
      const response = await CommentService.updateComment(commentId, { content });
      if (response.success && response.data) {
        setComments(prev => prev.map(comment => 
          comment.id === commentId ? response.data!.comment : comment
        ));
        toast.success('Comment updated');
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to update comment');
    }
  };

  // Delete comment
  const deleteComment = async (commentId: string) => {
    try {
      const response = await CommentService.deleteComment(commentId);
      if (response.success) {
        setComments(prev => prev.filter(comment => comment.id !== commentId));
        toast.success('Comment deleted');
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to delete comment');
    }
  };

  // Resolve comment
  const resolveComment = async (commentId: string) => {
    try {
      const response = await CommentService.resolveComment(commentId);
      if (response.success && response.data) {
        setComments(prev => prev.map(comment => 
          comment.id === commentId ? response.data!.comment : comment
        ));
        toast.success('Comment resolved');
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to resolve comment');
    }
  };

  // Connect to page WebSocket
  const connectToPage = (pageId: string) => {
    if (wsConnection) {
      wsConnection.close();
    }

    const ws = PubSubService.subscribeToPage(
      pageId,
      handleWebSocketMessage,
      handleWebSocketError,
      handleWebSocketClose
    );

    setWsConnection(ws);
  };

  // Disconnect from page WebSocket
  const disconnectFromPage = () => {
    if (wsConnection) {
      wsConnection.close();
      setWsConnection(null);
    }
  };

  // Broadcast typing indicator
  const broadcastTyping = async (blockId: string, isTyping: boolean) => {
    if (wsConnection && currentPage) {
      try {
        await PubSubService.broadcastTyping(`page_${currentPage.id}`, {
          user_id: 'current_user', // TODO: Get from auth context
          is_typing: isTyping,
          block_id: blockId
        });
      } catch (error) {
        console.error('Failed to broadcast typing indicator:', error);
      }
    }
  };

  // Broadcast cursor position
  const broadcastCursorPosition = async (blockId: string, position: number) => {
    if (wsConnection && currentPage) {
      try {
        await PubSubService.broadcastCursor(`page_${currentPage.id}`, {
          user_id: 'current_user', // TODO: Get from auth context
          block_id: blockId,
          position
        });
      } catch (error) {
        console.error('Failed to broadcast cursor position:', error);
      }
    }
  };

  // Handle WebSocket messages
  const handleWebSocketMessage = (message: PubSubMessage) => {
    switch (message.message) {
      case 'block_updated':
        if (message.data?.block_id && message.data?.content) {
          setBlocks(prev => prev.map(block => 
            block.id === message.data.block_id 
              ? { ...block, content: message.data.content }
              : block
          ));
        }
        break;
      
      case 'block_created':
        if (message.data?.block) {
          setBlocks(prev => [...prev, message.data.block]);
        }
        break;
      
      case 'block_deleted':
        if (message.data?.block_id) {
          setBlocks(prev => prev.filter(block => block.id !== message.data.block_id));
        }
        break;
      
      case 'comment_created':
        if (message.data?.comment) {
          setComments(prev => [...prev, message.data.comment]);
        }
        break;
      
      case 'comment_updated':
        if (message.data?.comment) {
          setComments(prev => prev.map(comment => 
            comment.id === message.data.comment.id ? message.data.comment : comment
          ));
        }
        break;
      
      case 'user_presence':
        if (message.data?.user_id && message.data?.status) {
          // Update active users list
          setActiveUsers(prev => {
            const filtered = prev.filter(u => u.id !== message.data.user_id);
            if (message.data.status === 'online') {
              return [...filtered, { id: message.data.user_id, status: 'online' }];
            }
            return filtered;
          });
        }
        break;
      
      case 'typing_indicator':
        // Handle typing indicators
        console.log('Typing indicator:', message.data);
        break;
      
      case 'cursor_position':
        // Handle cursor position updates
        console.log('Cursor position:', message.data);
        break;
    }
  };

  const handleWebSocketError = (error: Event) => {
    console.error('WebSocket error:', error);
    toast.error('Connection error. Some features may not work properly.');
  };

  const handleWebSocketClose = (event: CloseEvent) => {
    console.log('WebSocket connection closed:', event);
    if (event.code !== 1000) { // Not a normal closure
      toast.warning('Connection lost. Attempting to reconnect...');
    }
  };

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      disconnectFromPage();
    };
  }, []);

  return (
    <PageEditorContext.Provider value={{
      currentPage,
      blocks,
      comments,
      loading,
      saving,
      wsConnection,
      activeUsers,
      loadPage,
      updatePageTitle,
      createBlock,
      updateBlock,
      deleteBlock,
      reorderBlocks,
      convertBlockType,
      createComment,
      updateComment,
      deleteComment,
      resolveComment,
      connectToPage,
      disconnectFromPage,
      broadcastTyping,
      broadcastCursorPosition,
    }}>
      {children}
    </PageEditorContext.Provider>
  );
}

export function usePageEditor() {
  const context = useContext(PageEditorContext);
  if (context === undefined) {
    throw new Error('usePageEditor must be used within a PageEditorProvider');
  }
  return context;
}