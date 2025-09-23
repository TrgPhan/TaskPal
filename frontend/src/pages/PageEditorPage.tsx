import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent } from '../components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Avatar, AvatarFallback } from '../components/ui/avatar';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { Separator } from '../components/ui/separator';
import { 
  FileText, 
  Plus, 
  Type, 
  Heading1,
  Heading2,
  Heading3,
  List,
  CheckSquare,
  Image,
  Code,
  Quote,
  Minus,
  Users,
  MessageSquare,
  Star,
  Share,
  MoreHorizontal,
  ChevronRight,
  Home,
  Save,
  Eye,
  Settings,
  GripVertical
} from 'lucide-react';
import { toast } from 'sonner';

interface Block {
  id: string;
  type: 'paragraph' | 'heading1' | 'heading2' | 'heading3' | 'bulleted-list' | 'numbered-list' | 'todo' | 'quote' | 'code' | 'divider' | 'image';
  content: string;
  metadata?: any;
}

interface Comment {
  id: string;
  user: string;
  content: string;
  timestamp: string;
  resolved: boolean;
}

interface Page {
  id: string;
  title: string;
  blocks: Block[];
  comments: Comment[];
  updated_at: string;
  is_favorite: boolean;
}

export default function PageEditorPage() {
  const { workspaceId, pageId } = useParams();
  const [page, setPage] = useState<Page | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeUsers, setActiveUsers] = useState<any[]>([]);
  const [showComments, setShowComments] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [selectedBlockId, setSelectedBlockId] = useState<string | null>(null);

  // Mock data
  useEffect(() => {
    const mockPage: Page = {
      id: pageId!,
      title: 'Product Roadmap 2025',
      blocks: [
        {
          id: '1',
          type: 'heading1',
          content: 'Product Roadmap 2025'
        },
        {
          id: '2',
          type: 'paragraph',
          content: 'This document outlines our product strategy and key initiatives for the upcoming year. We\'ll focus on user experience improvements, performance optimizations, and new feature development.'
        },
        {
          id: '3',
          type: 'heading2',
          content: 'Q1 2025 Objectives'
        },
        {
          id: '4',
          type: 'todo',
          content: 'Launch mobile app redesign',
          metadata: { completed: false }
        },
        {
          id: '5',
          type: 'todo',
          content: 'Implement real-time collaboration',
          metadata: { completed: true }
        },
        {
          id: '6',
          type: 'todo',
          content: 'Add advanced search functionality',
          metadata: { completed: false }
        },
        {
          id: '7',
          type: 'quote',
          content: 'Focus on what matters most to our users and deliver exceptional value through every interaction.'
        },
        {
          id: '8',
          type: 'heading2',
          content: 'Technical Architecture'
        },
        {
          id: '9',
          type: 'code',
          content: 'const roadmap = {\n  q1: ["mobile-redesign", "real-time-collab"],\n  q2: ["advanced-search", "api-v2"],\n  q3: ["ai-features", "performance-boost"],\n  q4: ["enterprise-features"]\n};'
        }
      ],
      comments: [
        {
          id: '1',
          user: 'John Doe',
          content: 'Should we prioritize the mobile redesign over real-time collaboration?',
          timestamp: '2025-01-20T10:30:00Z',
          resolved: false
        },
        {
          id: '2',
          user: 'Jane Smith',
          content: 'Great progress on the collaboration features!',
          timestamp: '2025-01-19T15:45:00Z',
          resolved: true
        }
      ],
      updated_at: '2025-01-21T09:15:00Z',
      is_favorite: true
    };

    const mockActiveUsers = [
      { id: '1', name: 'John Doe', avatar: 'JD', cursor_position: 2 },
      { id: '2', name: 'Jane Smith', avatar: 'JS', cursor_position: 5 }
    ];

    setTimeout(() => {
      setPage(mockPage);
      setActiveUsers(mockActiveUsers);
      setLoading(false);
    }, 1000);
  }, [pageId]);

  const addBlock = (type: Block['type'], afterBlockId?: string) => {
    if (!page) return;

    const newBlock: Block = {
      id: Date.now().toString(),
      type,
      content: '',
      metadata: type === 'todo' ? { completed: false } : undefined
    };

    const newBlocks = [...page.blocks];
    
    if (afterBlockId) {
      const index = newBlocks.findIndex(block => block.id === afterBlockId);
      newBlocks.splice(index + 1, 0, newBlock);
    } else {
      newBlocks.push(newBlock);
    }

    setPage(prev => prev ? { ...prev, blocks: newBlocks } : null);
    setSelectedBlockId(newBlock.id);
  };

  const updateBlock = (blockId: string, content: string) => {
    if (!page) return;

    setPage(prev => prev ? {
      ...prev,
      blocks: prev.blocks.map(block =>
        block.id === blockId ? { ...block, content } : block
      )
    } : null);
  };

  const toggleTodo = (blockId: string) => {
    if (!page) return;

    setPage(prev => prev ? {
      ...prev,
      blocks: prev.blocks.map(block =>
        block.id === blockId && block.type === 'todo'
          ? { 
              ...block, 
              metadata: { 
                ...block.metadata, 
                completed: !block.metadata?.completed 
              } 
            }
          : block
      )
    } : null);
  };

  const deleteBlock = (blockId: string) => {
    if (!page) return;

    setPage(prev => prev ? {
      ...prev,
      blocks: prev.blocks.filter(block => block.id !== blockId)
    } : null);
  };

  const savePage = async () => {
    setSaving(true);
    
    try {
      // Mock API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setPage(prev => prev ? {
        ...prev,
        updated_at: new Date().toISOString()
      } : null);
      
      toast.success('Page saved successfully!');
    } catch (error) {
      toast.error('Failed to save page');
    } finally {
      setSaving(false);
    }
  };

  const addComment = () => {
    if (!newComment.trim() || !page) return;

    const comment: Comment = {
      id: Date.now().toString(),
      user: 'Current User',
      content: newComment,
      timestamp: new Date().toISOString(),
      resolved: false
    };

    setPage(prev => prev ? {
      ...prev,
      comments: [...prev.comments, comment]
    } : null);

    setNewComment('');
    toast.success('Comment added!');
  };

  const renderBlock = (block: Block) => {
    const isSelected = selectedBlockId === block.id;
    
    const blockContent = (
      <div 
        className={`group relative rounded-md transition-all ${
          isSelected ? 'bg-accent' : 'hover:bg-accent/50'
        }`}
        onClick={() => setSelectedBlockId(block.id)}
      >
        <div className="absolute left-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <GripVertical className="w-4 h-4 text-muted-foreground cursor-grab" />
        </div>
        
        <div className="pl-8 pr-4 py-2">
          {block.type === 'paragraph' && (
            <Textarea
              value={block.content}
              onChange={(e) => updateBlock(block.id, e.target.value)}
              placeholder="Type something..."
              className="min-h-[40px] resize-none border-0 bg-transparent p-0 focus:ring-0"
            />
          )}
          
          {block.type === 'heading1' && (
            <Input
              value={block.content}
              onChange={(e) => updateBlock(block.id, e.target.value)}
              placeholder="Heading 1"
              className="text-2xl font-semibold border-0 bg-transparent p-0 focus:ring-0"
            />
          )}
          
          {block.type === 'heading2' && (
            <Input
              value={block.content}
              onChange={(e) => updateBlock(block.id, e.target.value)}
              placeholder="Heading 2"
              className="text-xl font-semibold border-0 bg-transparent p-0 focus:ring-0"
            />
          )}
          
          {block.type === 'heading3' && (
            <Input
              value={block.content}
              onChange={(e) => updateBlock(block.id, e.target.value)}
              placeholder="Heading 3"
              className="text-lg font-semibold border-0 bg-transparent p-0 focus:ring-0"
            />
          )}
          
          {block.type === 'todo' && (
            <div className="flex items-start space-x-2">
              <button
                onClick={() => toggleTodo(block.id)}
                className={`mt-1 w-4 h-4 rounded border ${
                  block.metadata?.completed
                    ? 'bg-primary border-primary text-primary-foreground'
                    : 'border-border'
                }`}
              >
                {block.metadata?.completed && <CheckSquare className="w-3 h-3" />}
              </button>
              <Input
                value={block.content}
                onChange={(e) => updateBlock(block.id, e.target.value)}
                placeholder="To-do"
                className={`border-0 bg-transparent p-0 focus:ring-0 ${
                  block.metadata?.completed ? 'line-through text-muted-foreground' : ''
                }`}
              />
            </div>
          )}
          
          {block.type === 'quote' && (
            <div className="border-l-4 border-primary pl-4">
              <Textarea
                value={block.content}
                onChange={(e) => updateBlock(block.id, e.target.value)}
                placeholder="Quote..."
                className="italic min-h-[40px] resize-none border-0 bg-transparent p-0 focus:ring-0"
              />
            </div>
          )}
          
          {block.type === 'code' && (
            <Textarea
              value={block.content}
              onChange={(e) => updateBlock(block.id, e.target.value)}
              placeholder="// Code block"
              className="font-mono text-sm bg-muted rounded-md min-h-[60px] resize-none border-0 p-2 focus:ring-0"
            />
          )}
          
          {block.type === 'divider' && (
            <Separator className="my-4" />
          )}
        </div>
        
        {isSelected && (
          <div className="absolute right-2 top-2 flex items-center space-x-1">
            <Dialog>
              <DialogTrigger asChild>
                <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                  <Plus className="w-3 h-3" />
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-sm">
                <DialogHeader>
                  <DialogTitle>Add Block</DialogTitle>
                </DialogHeader>
                <div className="grid grid-cols-2 gap-2">
                  <Button variant="outline" size="sm" onClick={() => addBlock('paragraph', block.id)}>
                    <Type className="w-4 h-4 mr-2" />
                    Text
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => addBlock('heading1', block.id)}>
                    <Heading1 className="w-4 h-4 mr-2" />
                    H1
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => addBlock('heading2', block.id)}>
                    <Heading2 className="w-4 h-4 mr-2" />
                    H2
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => addBlock('heading3', block.id)}>
                    <Heading3 className="w-4 h-4 mr-2" />
                    H3
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => addBlock('todo', block.id)}>
                    <CheckSquare className="w-4 h-4 mr-2" />
                    To-do
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => addBlock('quote', block.id)}>
                    <Quote className="w-4 h-4 mr-2" />
                    Quote
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => addBlock('code', block.id)}>
                    <Code className="w-4 h-4 mr-2" />
                    Code
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => addBlock('divider', block.id)}>
                    <Minus className="w-4 h-4 mr-2" />
                    Divider
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
            
            <Button 
              variant="ghost" 
              size="sm" 
              className="h-6 w-6 p-0 text-destructive hover:text-destructive"
              onClick={() => deleteBlock(block.id)}
            >
              ×
            </Button>
          </div>
        )}
      </div>
    );

    return (
      <div key={block.id} className="mb-1">
        {blockContent}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-background/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-sm">
              <Link to="/dashboard" className="text-muted-foreground hover:text-foreground">
                <Home className="w-4 h-4" />
              </Link>
              <ChevronRight className="w-4 h-4 text-muted-foreground" />
              <Link 
                to={`/workspace/${workspaceId}`}
                className="text-muted-foreground hover:text-foreground"
              >
                Product Team
              </Link>
              <ChevronRight className="w-4 h-4 text-muted-foreground" />
              <span className="font-medium">{page?.title}</span>
            </div>

            <div className="flex items-center space-x-4">
              {/* Active Users */}
              <div className="flex items-center space-x-2">
                {activeUsers.map(user => (
                  <Avatar key={user.id} className="w-6 h-6">
                    <AvatarFallback className="text-xs">{user.avatar}</AvatarFallback>
                  </Avatar>
                ))}
                <span className="text-xs text-muted-foreground">
                  {activeUsers.length} online
                </span>
              </div>

              <div className="flex items-center space-x-2">
                <Button variant="ghost" size="sm" onClick={() => setShowComments(!showComments)}>
                  <MessageSquare className="w-4 h-4 mr-2" />
                  Comments ({page?.comments.length || 0})
                </Button>
                
                <Button variant="ghost" size="sm">
                  <Star className="w-4 h-4" />
                </Button>
                
                <Button variant="ghost" size="sm">
                  <Share className="w-4 h-4" />
                </Button>
                
                <Button variant="ghost" size="sm">
                  <Eye className="w-4 h-4" />
                </Button>
                
                <Button variant="ghost" size="sm">
                  <Settings className="w-4 h-4" />
                </Button>
                
                <Button onClick={savePage} disabled={saving}>
                  {saving ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  ) : (
                    <Save className="w-4 h-4" />
                  )}
                  {saving ? 'Saving...' : 'Save'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Main Editor */}
        <div className="flex-1 max-w-4xl mx-auto p-6">
          <div className="space-y-2">
            {page?.blocks.map(renderBlock)}
            
            {/* Add Block Button */}
            <div className="py-4">
              <Dialog>
                <DialogTrigger asChild>
                  <Button variant="ghost" className="text-muted-foreground">
                    <Plus className="w-4 h-4 mr-2" />
                    Add a block
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-sm">
                  <DialogHeader>
                    <DialogTitle>Add Block</DialogTitle>
                  </DialogHeader>
                  <div className="grid grid-cols-2 gap-2">
                    <Button variant="outline" size="sm" onClick={() => addBlock('paragraph')}>
                      <Type className="w-4 h-4 mr-2" />
                      Text
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => addBlock('heading1')}>
                      <Heading1 className="w-4 h-4 mr-2" />
                      H1
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => addBlock('heading2')}>
                      <Heading2 className="w-4 h-4 mr-2" />
                      H2
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => addBlock('heading3')}>
                      <Heading3 className="w-4 h-4 mr-2" />
                      H3
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => addBlock('todo')}>
                      <CheckSquare className="w-4 h-4 mr-2" />
                      To-do
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => addBlock('quote')}>
                      <Quote className="w-4 h-4 mr-2" />
                      Quote
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => addBlock('code')}>
                      <Code className="w-4 h-4 mr-2" />
                      Code
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => addBlock('divider')}>
                      <Minus className="w-4 h-4 mr-2" />
                      Divider
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          </div>
        </div>

        {/* Comments Sidebar */}
        {showComments && (
          <div className="w-80 border-l bg-background/50">
            <div className="p-4 border-b">
              <h3 className="font-medium">Comments</h3>
            </div>
            
            <div className="flex-1 p-4 space-y-4">
              {page?.comments.map(comment => (
                <div key={comment.id} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{comment.user}</span>
                    <Badge variant={comment.resolved ? 'default' : 'secondary'}>
                      {comment.resolved ? 'Resolved' : 'Open'}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">{comment.content}</p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(comment.timestamp).toLocaleDateString()}
                  </p>
                </div>
              ))}
              
              <div className="mt-6 space-y-2">
                <Textarea
                  placeholder="Add a comment..."
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                />
                <Button onClick={addComment} size="sm" className="w-full">
                  Add Comment
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}