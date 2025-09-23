# 📚 Hướng dẫn phát triển hệ thống RENotion

## 🎯 Tổng quan Database Schema

Hệ thống RENotion được thiết kế với 6 thành phần chính:

### 1. **Users & Authentication** 
- `User`: Quản lý người dùng và xác thực
- Hỗ trợ avatar, timezone, ngôn ngữ và trạng thái hoạt động

### 2. **Workspaces**
- `Workspace`: Không gian làm việc cho teams
- `WorkspaceMember`: Quản lý thành viên với roles (owner, admin, member, guest)
- Hỗ trợ invite codes và custom domains

### 3. **Pages & Content**
- `Page`: Trang nội dung với hệ thống phân cấp (parent-child)
- `PageTemplate`: Mẫu trang có sẵn
- `PagePermission`: Quản lý quyền truy cập chi tiết

### 4. **Blocks & Rich Content**
- `Block`: Khối nội dung (paragraph, heading, list, image, etc.)
- `BlockHistory`: Lịch sử thay đổi blocks (version control)
- Hỗ trợ 20+ loại block giống Notion

### 5. **Comments & Collaboration**
- `Comment`: Bình luận trên page/block với threading
- `CommentReaction`: Reactions (emoji) cho comments
- `CommentMention`: @mentions với notifications

### 6. **Database System**
- `Database`: Cơ sở dữ liệu Notion-style
- `DatabaseProperty`: Thuộc tính cột (15+ types)
- `DatabaseRow`: Hàng dữ liệu (mỗi row là 1 page)
- `DatabasePropertyValue`: Giá trị ô dữ liệu
- `DatabaseView`: Views (table, board, calendar, etc.)

---

## 🚀 Roadmap phát triển

### Phase 1: Core Backend Setup (Tuần 1-2)

#### Bước 1: Setup Flask Application Structure
```bash
# 1. Cập nhật requirements.txt
pip install flask flask-sqlalchemy flask-migrate flask-jwt-extended flask-cors python-dotenv

# 2. Tạo structure
mkdir app/services app/utils
touch app/services/__init__.py app/utils/__init__.py
```

#### Bước 2: Database Configuration
- Cập nhật `config.py`:
  - Database URL (PostgreSQL recommended)
  - JWT Secret Key
  - File upload settings
  - CORS configuration

#### Bước 3: Database Migration
```bash
# Initialize migration
flask db init

# Create initial migration
flask db migrate -m "Initial migration with all models"

# Apply migration
flask db upgrade
```

#### Bước 4: Create Services Layer
Tạo các service files:
- `app/services/user_service.py` - User management
- `app/services/workspace_service.py` - Workspace operations
- `app/services/page_service.py` - Page CRUD operations
- `app/services/block_service.py` - Block management
- `app/services/database_service.py` - Database operations

### Phase 2: Authentication & User Management (Tuần 3)

#### Bước 1: Authentication System
- JWT-based authentication
- Registration & Login endpoints
- Password reset functionality
- User profile management

#### Bước 2: Workspace Management
- Create/join workspace
- Invite system with codes
- Role-based permissions
- Member management

### Phase 3: Core Content System (Tuần 4-6)

#### Bước 1: Page Management
- CRUD operations for pages
- Hierarchical structure (parent-child)
- Permission system
- Template system

#### Bước 2: Block System
- Rich text editor integration
- 20+ block types implementation
- Drag & drop reordering
- Version history

#### Bước 3: Real-time Collaboration
- WebSocket integration
- Live editing
- User presence indicators
- Conflict resolution

### Phase 4: Advanced Features (Tuần 7-10)

#### Bước 1: Comment System
- Threading comments
- Reactions & mentions
- Real-time notifications
- Comment resolution

#### Bước 2: Database Features
- Property type implementations
- Views (table, board, calendar)
- Filters and sorting
- Relations between databases

#### Bước 3: Search & Analytics
- Full-text search
- Advanced filtering
- Usage analytics
- Performance monitoring

### Phase 5: Frontend Development (Tuần 11-16)

#### Recommended Tech Stack:
- **Framework**: React.js với TypeScript
- **State Management**: Redux Toolkit hoặc Zustand
- **UI Components**: 
  - Rich text editor: Draft.js hoặc Slate.js
  - Drag & drop: @dnd-kit
  - UI Library: Ant Design hoặc Chakra UI
- **Real-time**: Socket.IO client

#### Core Components cần phát triển:
1. **Authentication Components**
   - Login/Register forms
   - Workspace selection
   - User profile

2. **Layout Components**
   - Sidebar navigation
   - Page tree view
   - Breadcrumb navigation

3. **Editor Components**
   - Rich text editor
   - Block components (20+ types)
   - Drag & drop interface

4. **Database Components**
   - Table view
   - Board/Kanban view
   - Calendar view
   - Property editors

### Phase 6: Production Optimization (Tuần 17-20)

#### Performance Optimizations:
- Database indexing strategy
- Caching layer (Redis)
- CDN for static assets
- Image optimization
- Query optimization

#### Security Enhancements:
- Rate limiting
- Input validation
- XSS protection
- CSRF protection
- File upload security

#### DevOps & Deployment:
- Docker containerization
- CI/CD pipeline
- Database backups
- Monitoring & logging
- Load balancing

---

## 🛠️ Technical Implementation Guidelines

### 1. API Design Principles
```python
# RESTful API structure
GET    /api/workspaces/{id}/pages          # List pages
POST   /api/workspaces/{id}/pages          # Create page
GET    /api/pages/{id}                     # Get page details
PUT    /api/pages/{id}                     # Update page
DELETE /api/pages/{id}                     # Delete page

# Nested resources
GET    /api/pages/{id}/blocks              # List blocks in page
POST   /api/pages/{id}/blocks              # Create block
PUT    /api/blocks/{id}                    # Update block
```

### 2. Error Handling Strategy
```python
# Standardized error responses
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input data",
        "details": {
            "field": "email",
            "issue": "Email already exists"
        }
    }
}
```

### 3. Permission System Implementation
```python
# Role hierarchy
PERMISSIONS = {
    'owner': ['read', 'write', 'delete', 'manage_members', 'manage_settings'],
    'admin': ['read', 'write', 'delete', 'manage_members'],
    'member': ['read', 'write', 'comment'],
    'guest': ['read', 'comment']
}
```

### 4. Real-time Features
```python
# WebSocket events
EVENTS = {
    'page_updated': 'Khi page được cập nhật',
    'block_created': 'Khi tạo block mới', 
    'block_updated': 'Khi cập nhật block',
    'user_joined': 'Khi user vào workspace',
    'cursor_moved': 'Khi di chuyển con trỏ'
}
```

### 5. Search Implementation
```python
# Full-text search fields
SEARCHABLE_FIELDS = {
    'pages': ['title', 'content_text'],
    'blocks': ['plain_text'],
    'comments': ['plain_text'],
    'database_rows': ['text_value']
}
```

---

## 📊 Database Performance Considerations

### Essential Indexes:
```sql
-- User lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- Page hierarchy
CREATE INDEX idx_pages_workspace_parent ON pages(workspace_id, parent_id);
CREATE INDEX idx_pages_path ON pages USING gin(path gin_trgm_ops);

-- Block ordering
CREATE INDEX idx_blocks_page_order ON blocks(page_id, order_index);

-- Database queries
CREATE INDEX idx_db_rows_database_created ON database_rows(database_id, created_at DESC);

-- Full-text search
CREATE INDEX idx_pages_search ON pages USING gin(to_tsvector('english', title || ' ' || coalesce(content_text, '')));
```

### Query Optimization:
1. **Lazy Loading**: Load blocks only when needed
2. **Pagination**: Implement cursor-based pagination
3. **Caching**: Cache frequently accessed pages
4. **Materialized Views**: For complex database queries

---

## 🔧 Development Tools & Testing

### Recommended Development Stack:
```bash
# Backend testing
pytest
pytest-flask
pytest-cov
factory-boy  # Test data factories

# Code quality
black        # Code formatting
flake8       # Linting
mypy         # Type checking
pre-commit   # Git hooks
```

### Testing Strategy:
1. **Unit Tests**: Service layer logic
2. **Integration Tests**: API endpoints
3. **Database Tests**: Model relationships
4. **Performance Tests**: Query optimization
5. **Security Tests**: Authentication & authorization

---

## 📈 Monitoring & Analytics

### Key Metrics to Track:
1. **User Engagement**
   - Daily/Monthly active users
   - Page views & edits
   - Collaboration sessions

2. **Performance Metrics**
   - API response times
   - Database query performance
   - Real-time connection stability

3. **Business Metrics**
   - Workspace creation rate
   - User retention
   - Feature usage patterns

### Tools Integration:
- **Logging**: Structured logging với ELK stack
- **Monitoring**: Prometheus + Grafana
- **Error Tracking**: Sentry
- **Analytics**: Custom dashboard

---

## 🚢 Deployment Architecture

### Production Environment:
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │────│   Web Servers   │────│   Database      │
│   (Nginx)       │    │   (Flask+uWSGI) │    │   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CDN           │    │   Cache         │    │   File Storage  │
│   (CloudFlare)  │    │   (Redis)       │    │   (AWS S3)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Docker Setup:
```dockerfile
# Example Dockerfile structure
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]
```

---

## ✅ Next Steps

### Immediate Actions (Next 1-2 days):
1. ✅ **Setup config.py** với database URL và JWT settings
2. ✅ **Update requirements.txt** với các dependencies cần thiết  
3. ✅ **Initialize database migrations**
4. ✅ **Create basic API structure** trong routes/

### Weekly Milestones:
- **Week 1**: Authentication system hoàn chỉnh
- **Week 2**: Workspace và Page management
- **Week 3**: Block system cơ bản
- **Week 4**: Real-time collaboration prototype
- **Week 8**: Database features MVP
- **Week 12**: Frontend prototype
- **Week 16**: Beta version ready
- **Week 20**: Production deployment

### Success Metrics:
- [ ] User có thể tạo account và workspace
- [ ] Tạo và chỉnh sửa pages với blocks
- [ ] Real-time collaboration hoạt động
- [ ] Database features cơ bản
- [ ] Search functionality
- [ ] Mobile responsive design
- [ ] Performance: <2s page load time
- [ ] 99.9% uptime in production

---

**Good luck với việc phát triển RENotion! 🚀**

*Nếu có câu hỏi hoặc cần hỗ trợ technical cụ thể, hãy liên hệ để được tư vấn chi tiết hơn.*
