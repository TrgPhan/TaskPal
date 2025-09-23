import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useWorkspace } from '../contexts/WorkspaceContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent } from '../components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Avatar, AvatarFallback } from '../components/ui/avatar';
import { Badge } from '../components/ui/badge';
import { Separator } from '../components/ui/separator';
import { ScrollArea } from '../components/ui/scroll-area';
import { 
  FileText, 
  Plus, 
  Search, 
  Settings, 
  Users, 
  ChevronRight,
  ChevronDown,
  Home,
  Star,
  Trash2,
  MoreHorizontal,
  Share,
  Edit
} from 'lucide-react';
import { toast } from 'sonner';

interface Page {
  id: string;
  title: string;
  content: string;
  parent_id: string | null;
  children: Page[];
  updated_at: string;
  is_favorite: boolean;
}

interface Workspace {
  id: string;
  name: string;
  description: string;
  role: 'owner' | 'admin' | 'member' | 'guest';
  members: any[];
}

export default function WorkspacePage() {
  const { workspaceId } = useParams();
  const { user } = useAuth();
  const { 
    currentWorkspace, 
    pages, 
    loading, 
    selectWorkspace, 
    createPage 
  } = useWorkspace();
  
  const [selectedPage, setSelectedPage] = useState<Page | null>(null);
  const [createPageDialog, setCreatePageDialog] = useState(false);
  const [expandedPages, setExpandedPages] = useState<Set<string>>(new Set());
  const [newPage, setNewPage] = useState({
    title: '',
    content: '',
    parent_id: null as string | null
  });

  // Load workspace and pages
  useEffect(() => {
    if (workspaceId) {
      selectWorkspace(workspaceId);
    }
  }, [workspaceId]);

  const handleCreatePage = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!workspaceId) return;
    
    const page = await createPage({
      workspace_id: workspaceId,
      title: newPage.title,
      parent_id: newPage.parent_id
    });
    
    if (page) {
      setNewPage({ title: '', content: '', parent_id: null });
      setCreatePageDialog(false);
    }
  };

  const updatePageChildren = (page: Page, parentId: string, newPage: Page): Page => {
    if (page.id === parentId) {
      return {
        ...page,
        children: [...page.children, newPage]
      };
    }
    return {
      ...page,
      children: page.children.map(child => updatePageChildren(child, parentId, newPage))
    };
  };

  const togglePageExpansion = (pageId: string) => {
    setExpandedPages(prev => {
      const newSet = new Set(prev);
      if (newSet.has(pageId)) {
        newSet.delete(pageId);
      } else {
        newSet.add(pageId);
      }
      return newSet;
    });
  };

  const renderPageTree = (pageList: Page[], level = 0) => {
    return pageList.map(page => (
      <div key={page.id}>
        <div 
          className={`flex items-center py-1 px-2 rounded-md hover:bg-accent cursor-pointer group ${
            selectedPage?.id === page.id ? 'bg-accent' : ''
          }`}
          style={{ paddingLeft: `${level * 16 + 8}px` }}
        >
          {page.children.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              className="w-4 h-4 p-0 mr-1"
              onClick={() => togglePageExpansion(page.id)}
            >
              {expandedPages.has(page.id) ? (
                <ChevronDown className="w-3 h-3" />
              ) : (
                <ChevronRight className="w-3 h-3" />
              )}
            </Button>
          )}
          
          <FileText className="w-4 h-4 mr-2 text-muted-foreground" />
          
          <Link
            to={`/workspace/${workspaceId}/page/${page.id}`}
            className="flex-1 text-sm truncate hover:text-foreground"
            onClick={() => setSelectedPage(page)}
          >
            {page.title}
          </Link>
          
          {page.is_favorite && (
            <Star className="w-3 h-3 text-yellow-500 fill-yellow-500" />
          )}
          
          <Button
            variant="ghost"
            size="sm"
            className="w-4 h-4 p-0 opacity-0 group-hover:opacity-100"
          >
            <MoreHorizontal className="w-3 h-3" />
          </Button>
        </div>
        
        {expandedPages.has(page.id) && page.children.length > 0 && (
          <div>
            {renderPageTree(page.children, level + 1)}
          </div>
        )}
      </div>
    ));
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <div className="w-80 border-r bg-background/50 flex flex-col">
        {/* Workspace Header */}
        <div className="p-4 border-b">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <Link to="/dashboard" className="text-muted-foreground hover:text-foreground">
                <Home className="w-4 h-4" />
              </Link>
              <ChevronRight className="w-4 h-4 text-muted-foreground" />
              <span className="font-medium">{currentWorkspace?.name || 'Loading...'}</span>
            </div>
            <Button variant="ghost" size="sm">
              <Settings className="w-4 h-4" />
            </Button>
          </div>
          
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search pages..."
              className="pl-10"
            />
          </div>
        </div>

        {/* Quick Actions */}
        <div className="p-4 border-b">
          <div className="space-y-2">
            <Dialog open={createPageDialog} onOpenChange={setCreatePageDialog}>
              <DialogTrigger asChild>
                <Button variant="outline" className="w-full justify-start">
                  <Plus className="w-4 h-4 mr-2" />
                  New Page
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Create New Page</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleCreatePage} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="title">Page Title</Label>
                    <Input
                      id="title"
                      placeholder="Enter page title"
                      value={newPage.title}
                      onChange={(e) => setNewPage(prev => ({ ...prev, title: e.target.value }))}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="content">Initial Content (Optional)</Label>
                    <Textarea
                      id="content"
                      placeholder="Start writing..."
                      value={newPage.content}
                      onChange={(e) => setNewPage(prev => ({ ...prev, content: e.target.value }))}
                    />
                  </div>
                  <div className="flex space-x-2 pt-4">
                    <Button type="submit" className="flex-1">Create Page</Button>
                    <Button type="button" variant="outline" onClick={() => setCreatePageDialog(false)}>
                      Cancel
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
            
            <Button variant="outline" className="w-full justify-start">
              <Share className="w-4 h-4 mr-2" />
              Invite Members
            </Button>
          </div>
        </div>

        {/* Page Tree */}
        <div className="flex-1 overflow-hidden">
          <div className="p-4">
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Pages</h3>
          </div>
          <ScrollArea className="flex-1 px-4">
            <div className="space-y-1">
              {pages.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <FileText className="w-8 h-8 mx-auto mb-2" />
                  <p className="text-sm">No pages yet</p>
                  <p className="text-xs">Create your first page to get started</p>
                </div>
              ) : (
                renderPageTree(pages)
              )}
            </div>
          </ScrollArea>
        </div>

        {/* Workspace Members */}
        <div className="p-4 border-t">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-muted-foreground">Members</h3>
            <Button variant="ghost" size="sm">
              <Users className="w-4 h-4" />
            </Button>
          </div>
          <div className="space-y-2">
            {currentWorkspace?.members?.slice(0, 3).map(member => (
              <div key={member.id} className="flex items-center space-x-2">
                <Avatar className="w-6 h-6">
                  <AvatarFallback className="text-xs">
                    {member.name.split(' ').map((n: string) => n[0]).join('')}
                  </AvatarFallback>
                </Avatar>
                <span className="text-sm flex-1 truncate">{member.name}</span>
                <Badge variant="secondary" className="text-xs">
                  {member.role}
                </Badge>
              </div>
            ))}
            {currentWorkspace && currentWorkspace.members && currentWorkspace.members.length > 3 && (
              <p className="text-xs text-muted-foreground">
                +{currentWorkspace.members.length - 3} more members
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {selectedPage ? (
          <>
            {/* Page Header */}
            <div className="border-b p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-2xl font-semibold mb-1">{selectedPage.title}</h1>
                  <p className="text-sm text-muted-foreground">
                    Last updated {formatDate(selectedPage.updated_at)}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <Button variant="ghost" size="sm">
                    <Star className="w-4 h-4" />
                  </Button>
                  <Button variant="ghost" size="sm">
                    <Share className="w-4 h-4" />
                  </Button>
                  <Button variant="ghost" size="sm">
                    <MoreHorizontal className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>

            {/* Page Content */}
            <div className="flex-1 p-6">
              <Card>
                <CardContent className="p-6">
                  <p className="text-muted-foreground mb-4">
                    {selectedPage.content || 'This page is empty. Click to start editing.'}
                  </p>
                  <Button variant="outline">
                    <Edit className="w-4 h-4 mr-2" />
                    Edit Page
                  </Button>
                </CardContent>
              </Card>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <FileText className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
              <h2 className="text-xl font-medium mb-2">Welcome to {currentWorkspace?.name || 'Workspace'}</h2>
              <p className="text-muted-foreground mb-4">
                Select a page from the sidebar or create a new one to get started.
              </p>
              <Dialog open={createPageDialog} onOpenChange={setCreatePageDialog}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="w-4 h-4 mr-2" />
                    Create Your First Page
                  </Button>
                </DialogTrigger>
              </Dialog>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}