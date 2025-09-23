import React, { createContext, useContext, useState, useEffect } from 'react';
import { WorkspaceService, Workspace } from '../services/workspaceService';
import { PageService, Page } from '../services/pageService';
import { PubSubService, PubSubMessage } from '../services/pubsubService';
import { toast } from 'sonner';

interface WorkspaceContextType {
  workspaces: Workspace[];
  currentWorkspace: Workspace | null;
  pages: Page[];
  loading: boolean;
  wsConnection: WebSocket | null;
  
  // Workspace operations
  fetchWorkspaces: () => Promise<void>;
  createWorkspace: (data: { name: string; description: string }) => Promise<Workspace | null>;
  selectWorkspace: (workspaceId: string) => Promise<void>;
  updateWorkspace: (workspaceId: string, data: Partial<Workspace>) => Promise<void>;
  deleteWorkspace: (workspaceId: string) => Promise<void>;
  
  // Page operations
  fetchPages: (workspaceId: string) => Promise<void>;
  createPage: (data: { workspace_id: string; title: string; parent_id?: string | null }) => Promise<Page | null>;
  updatePage: (pageId: string, data: Partial<Page>) => Promise<void>;
  deletePage: (pageId: string) => Promise<void>;
  
  // Real-time features
  connectToWorkspace: (workspaceId: string) => void;
  disconnectFromWorkspace: () => void;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [currentWorkspace, setCurrentWorkspace] = useState<Workspace | null>(null);
  const [pages, setPages] = useState<Page[]>([]);
  const [loading, setLoading] = useState(false);
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);

  // Fetch user's workspaces
  const fetchWorkspaces = async () => {
    setLoading(true);
    try {
      const response = await WorkspaceService.getWorkspaces();
      if (response.success && response.data) {
        setWorkspaces(response.data.workspaces);
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to fetch workspaces');
    } finally {
      setLoading(false);
    }
  };

  // Create new workspace
  const createWorkspace = async (data: { name: string; description: string }): Promise<Workspace | null> => {
    try {
      const response = await WorkspaceService.createWorkspace(data);
      if (response.success && response.data) {
        const newWorkspace = response.data.workspace;
        setWorkspaces(prev => [newWorkspace, ...prev]);
        toast.success('Workspace created successfully!');
        return newWorkspace;
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to create workspace');
    }
    return null;
  };

  // Select and load workspace
  const selectWorkspace = async (workspaceId: string) => {
    setLoading(true);
    try {
      const response = await WorkspaceService.getWorkspaceById(workspaceId);
      if (response.success && response.data) {
        setCurrentWorkspace(response.data.workspace);
        await fetchPages(workspaceId);
        connectToWorkspace(workspaceId);
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to load workspace');
    } finally {
      setLoading(false);
    }
  };

  // Update workspace
  const updateWorkspace = async (workspaceId: string, data: Partial<Workspace>) => {
    try {
      const response = await WorkspaceService.updateWorkspace(workspaceId, data);
      if (response.success && response.data) {
        const updatedWorkspace = response.data.workspace;
        setWorkspaces(prev => prev.map(ws => 
          ws.id === workspaceId ? updatedWorkspace : ws
        ));
        if (currentWorkspace?.id === workspaceId) {
          setCurrentWorkspace(updatedWorkspace);
        }
        toast.success('Workspace updated successfully!');
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to update workspace');
    }
  };

  // Delete workspace
  const deleteWorkspace = async (workspaceId: string) => {
    try {
      const response = await WorkspaceService.deleteWorkspace(workspaceId);
      if (response.success) {
        setWorkspaces(prev => prev.filter(ws => ws.id !== workspaceId));
        if (currentWorkspace?.id === workspaceId) {
          setCurrentWorkspace(null);
          setPages([]);
        }
        toast.success('Workspace deleted successfully!');
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to delete workspace');
    }
  };

  // Fetch pages for workspace
  const fetchPages = async (workspaceId: string) => {
    try {
      const response = await PageService.getPagesByWorkspace(workspaceId);
      if (response.success && response.data) {
        // Transform flat list to hierarchical structure
        const flatPages = response.data.pages;
        const hierarchicalPages = buildPageHierarchy(flatPages);
        setPages(hierarchicalPages);
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to fetch pages');
    }
  };

  // Create new page
  const createPage = async (data: { workspace_id: string; title: string; parent_id?: string | null }): Promise<Page | null> => {
    try {
      const response = await PageService.createPage(data);
      if (response.success && response.data) {
        const newPage = { ...response.data.page, children: [] };
        
        if (data.parent_id) {
          // Add as child to parent page
          setPages(prev => updatePageChildren(prev, data.parent_id!, newPage));
        } else {
          // Add as root page
          setPages(prev => [...prev, newPage]);
        }
        
        toast.success('Page created successfully!');
        return newPage;
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to create page');
    }
    return null;
  };

  // Update page
  const updatePage = async (pageId: string, data: Partial<Page>) => {
    try {
      const response = await PageService.updatePage(pageId, data);
      if (response.success && response.data) {
        const updatedPage = response.data.page;
        setPages(prev => updatePageInHierarchy(prev, pageId, updatedPage));
        toast.success('Page updated successfully!');
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to update page');
    }
  };

  // Delete page
  const deletePage = async (pageId: string) => {
    try {
      const response = await PageService.deletePage(pageId);
      if (response.success) {
        setPages(prev => removePageFromHierarchy(prev, pageId));
        toast.success('Page deleted successfully!');
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to delete page');
    }
  };

  // Connect to workspace WebSocket
  const connectToWorkspace = (workspaceId: string) => {
    if (wsConnection) {
      wsConnection.close();
    }

    const ws = PubSubService.subscribeToWorkspace(
      workspaceId,
      handleWebSocketMessage,
      handleWebSocketError,
      handleWebSocketClose
    );

    setWsConnection(ws);
  };

  // Disconnect from workspace WebSocket
  const disconnectFromWorkspace = () => {
    if (wsConnection) {
      wsConnection.close();
      setWsConnection(null);
    }
  };

  // Handle WebSocket messages
  const handleWebSocketMessage = (message: PubSubMessage) => {
    switch (message.message) {
      case 'page_created':
        if (message.data?.page) {
          const newPage = { ...message.data.page, children: [] };
          if (newPage.parent_id) {
            setPages(prev => updatePageChildren(prev, newPage.parent_id!, newPage));
          } else {
            setPages(prev => [...prev, newPage]);
          }
        }
        break;
      
      case 'page_updated':
        if (message.data?.page) {
          setPages(prev => updatePageInHierarchy(prev, message.data.page.id, message.data.page));
        }
        break;
      
      case 'page_deleted':
        if (message.data?.page_id) {
          setPages(prev => removePageFromHierarchy(prev, message.data.page_id));
        }
        break;
      
      case 'workspace_updated':
        if (message.data?.workspace && currentWorkspace) {
          setCurrentWorkspace(message.data.workspace);
        }
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
      // Implement reconnection logic if needed
    }
  };

  // Helper functions
  const buildPageHierarchy = (flatPages: Page[]): Page[] => {
    const pageMap = new Map<string, Page>();
    const rootPages: Page[] = [];

    // First pass: create map and initialize children arrays
    flatPages.forEach(page => {
      pageMap.set(page.id, { ...page, children: [] });
    });

    // Second pass: build hierarchy
    flatPages.forEach(page => {
      const pageWithChildren = pageMap.get(page.id)!;
      
      if (page.parent_id) {
        const parent = pageMap.get(page.parent_id);
        if (parent) {
          parent.children!.push(pageWithChildren);
        }
      } else {
        rootPages.push(pageWithChildren);
      }
    });

    return rootPages;
  };

  const updatePageChildren = (pages: Page[], parentId: string, newPage: Page): Page[] => {
    return pages.map(page => {
      if (page.id === parentId) {
        return {
          ...page,
          children: [...(page.children || []), newPage]
        };
      }
      return {
        ...page,
        children: page.children ? updatePageChildren(page.children, parentId, newPage) : []
      };
    });
  };

  const updatePageInHierarchy = (pages: Page[], pageId: string, updatedPage: Partial<Page>): Page[] => {
    return pages.map(page => {
      if (page.id === pageId) {
        return { ...page, ...updatedPage };
      }
      return {
        ...page,
        children: page.children ? updatePageInHierarchy(page.children, pageId, updatedPage) : []
      };
    });
  };

  const removePageFromHierarchy = (pages: Page[], pageId: string): Page[] => {
    return pages.filter(page => page.id !== pageId).map(page => ({
      ...page,
      children: page.children ? removePageFromHierarchy(page.children, pageId) : []
    }));
  };

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      disconnectFromWorkspace();
    };
  }, []);

  return (
    <WorkspaceContext.Provider value={{
      workspaces,
      currentWorkspace,
      pages,
      loading,
      wsConnection,
      fetchWorkspaces,
      createWorkspace,
      selectWorkspace,
      updateWorkspace,
      deleteWorkspace,
      fetchPages,
      createPage,
      updatePage,
      deletePage,
      connectToWorkspace,
      disconnectFromWorkspace,
    }}>
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (context === undefined) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider');
  }
  return context;
}