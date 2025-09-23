# TaskPal API Endpoints

## 1. Auth (Xác thực)

### Đăng ký
- **POST** `/api/auth/register`
- **Body:**
```json
{
  "email": "abc@13579.com",
  "username": "abc13579",
  "full_name": "Tên của bạn",
  "password": "132442"
}
```
- **Output:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "a4cff7e6-76f6-4f62-b89c-9a5c30aa4c21",
      "email": "abc@13579.com",
      "username": "abc13579",
      "full_name": "Tên của bạn",
      "created_at": "2025-09-23T06:57:39.602345",
      "is_active": true,
      "is_verified": false,
      "language": "vi",
      "timezone": "UTC"
    },
    "message": "User registered successfully"
  },
  "message": "Success"
}
```

### Đăng nhập
- **POST** `/api/auth/login`
- **Body:**
```json
{
  "email": "abc@13579.com",
  "password": "132442"
}
```
- **Output:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "a4cff7e6-76f6-4f62-b89c-9a5c30aa4c21",
      "email": "abc@13579.com",
      "username": "abc13579",
      "full_name": "Tên của bạn",
      "created_at": "2025-09-23T06:57:39.602345",
      "is_active": true,
      "is_verified": false,
      "language": "vi",
      "timezone": "UTC"
    },
    "message": "Login successful"
  },
  "message": "Success"
}
```

### Đăng xuất
- **POST** `/api/auth/logout`
- **Header:** `Authorization: Bearer <access_token>`
- **Output:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

### Làm mới token
- **POST** `/api/auth/refresh`
- **Header:** `Authorization: Bearer <access_token>`
- **Output:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  },
  "message": "Token refreshed"
}
```

### Lấy thông tin user hiện tại
- **GET** `/api/auth/me`
- **Header:** `Authorization: Bearer <access_token>`
- **Output:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "a4cff7e6-76f6-4f62-b89c-9a5c30aa4c21",
      "email": "abc@13579.com",
      "username": "abc13579",
      "full_name": "Tên của bạn",
      "created_at": "2025-09-23T06:57:39.602345",
      "is_active": true,
      "is_verified": false,
      "language": "vi",
      "timezone": "UTC"
    }
  },
  "message": "User info"
}
```

---

## 2. User

### Lấy profile
- **GET** `/api/user/profile`
- **Header:** `Authorization: Bearer <access_token>`
- **Output:**
```json
{
  "success": true,
  "data": {
    "profile": {
      "id": "a4cff7e6-76f6-4f62-b89c-9a5c30aa4c21",
      "email": "abc@13579.com",
      "username": "abc13579",
      "full_name": "Tên của bạn",
      "created_at": "2025-09-23T06:57:39.602345",
      "is_active": true,
      "is_verified": false,
      "language": "vi",
      "timezone": "UTC"
    }
  },
  "message": "Profile info"
}
```

### Cập nhật profile
- **PUT** `/api/user/profile`
- **Header:** `Authorization: Bearer <access_token>`
- **Body:**
```json
{
  "full_name": "Tên mới",
  "timezone": "Asia/Ho_Chi_Minh"
}
```
- **Output:**
```json
{
  "success": true,
  "data": {
    "profile": {
      "id": "a4cff7e6-76f6-4f62-b89c-9a5c30aa4c21",
      "email": "abc@13579.com",
      "username": "abc13579",
      "full_name": "Tên mới",
      "created_at": "2025-09-23T06:57:39.602345",
      "is_active": true,
      "is_verified": false,
      "language": "vi",
      "timezone": "Asia/Ho_Chi_Minh"
    }
  },
  "message": "Profile updated"
}
```

### Lấy settings
- **GET** `/api/user/settings`
- **Header:** `Authorization: Bearer <access_token>`
- **Output:**
```json
{
  "success": true,
  "data": {
    "settings": {
      "theme": "dark",
      "notification": true
    }
  },
  "message": "User settings"
}
```

### Cập nhật settings
- **PUT** `/api/user/settings`
- **Header:** `Authorization: Bearer <access_token>`
- **Body:**
```json
{
  "theme": "dark",
  "notification": true
}
```
- **Output:**
```json
{
  "success": true,
  "data": {
    "settings": {
      "theme": "dark",
      "notification": true
    }
  },
  "message": "Settings updated"
}
```

---

## 3. Workspace

### Tạo workspace
- **POST** `/api/workspace/`
- **Header:** `Authorization: Bearer <access_token>`
- **Body:**
```json
{
  "name": "Workspace 1",
  "description": "Mô tả workspace"
}
```

### Lấy danh sách workspace
- **GET** `/api/workspace/`
- **Header:** `Authorization: Bearer <access_token>`

### Lấy workspace theo id
- **GET** `/api/workspace/<workspace_id>`
- **Header:** `Authorization: Bearer <access_token>`

### Cập nhật workspace
- **PUT** `/api/workspace/<workspace_id>`
- **Header:** `Authorization: Bearer <access_token>`
- **Body:**
```json
{
  "name": "Tên mới",
  "description": "Mô tả mới"
}
```

### Xóa workspace
- **DELETE** `/api/workspace/<workspace_id>`
- **Header:** `Authorization: Bearer <access_token>`

### Mời thành viên
- **POST** `/api/workspace/<workspace_id>/members`
- **Header:** `Authorization: Bearer <access_token>`
- **Body:**
```json
{
  "email": "user2@email.com",
  "role": "member"
}
```

### Cập nhật vai trò thành viên
- **PUT** `/api/workspace/<workspace_id>/members/<user_id>`
- **Header:** `Authorization: Bearer <access_token>`
- **Body:**
```json
{
  "role": "admin"
}
```

### Xóa thành viên
- **DELETE** `/api/workspace/<workspace_id>/members/<user_id>`
- **Header:** `Authorization: Bearer <access_token>`

### Tham gia workspace bằng mã mời
- **POST** `/api/workspace/join/<invite_code>`
- **Header:** `Authorization: Bearer <access_token>`

### Rời workspace
- **POST** `/api/workspace/<workspace_id>/leave`
- **Header:** `Authorization: Bearer <access_token>`

---

## 4. Workspace

### Tạo workspace
- **POST** `/api/workspace/`
- **Body:**
```json
{
  "name": "Workspace 1",
  "description": "Mô tả workspace"
}
```
- **Output:**
```json
{
  "success": true,
  "data": {
    "workspace": {
      "id": "ws_123",
      "name": "Workspace 1",
      "description": "Mô tả workspace",
      "created_at": "2025-09-23T07:00:00.000000",
      "owner_id": "user_123"
    }
  },
  "message": "Workspace created"
}
```

### Lấy danh sách workspace
- **GET** `/api/workspace/`
- **Output:**
```json
{
  "success": true,
  "data": {
    "workspaces": [
      {
        "id": "ws_123",
        "name": "Workspace 1",
        "description": "Mô tả workspace",
        "created_at": "2025-09-23T07:00:00.000000",
        "owner_id": "user_123"
      }
    ]
  },
  "message": "Workspace list"
}
```

### Lấy workspace theo id
- **GET** `/api/workspace/<workspace_id>`
- **Output:**
```json
{
  "success": true,
  "data": {
    "workspace": {
      "id": "ws_123",
      "name": "Workspace 1",
      "description": "Mô tả workspace",
      "created_at": "2025-09-23T07:00:00.000000",
      "owner_id": "user_123"
    }
  },
  "message": "Workspace info"
}
```

---

## 5. Page

### Tạo page
- **POST** `/api/page/`
- **Body:**
```json
{
  "workspace_id": "ws_123",
  "title": "Trang đầu tiên",
  "parent_id": null
}
```
- **Output:**
```json
{
  "success": true,
  "data": {
    "page": {
      "id": "page_123",
      "workspace_id": "ws_123",
      "title": "Trang đầu tiên",
      "parent_id": null,
      "created_at": "2025-09-23T07:10:00.000000"
    }
  },
  "message": "Page created"
}
```

### Lấy danh sách page trong workspace
- **GET** `/api/page/?workspace_id=ws_123`
- **Output:**
```json
{
  "success": true,
  "data": {
    "pages": [
      {
        "id": "page_123",
        "workspace_id": "ws_123",
        "title": "Trang đầu tiên",
        "parent_id": null,
        "created_at": "2025-09-23T07:10:00.000000"
      }
    ]
  },
  "message": "Page list"
}
```

---

## 6. Block

### Tạo block
- **POST** `/api/block/`
- **Body:**
```json
{
  "page_id": "page_123",
  "type": "text",
  "content": "Nội dung block"
}
```
- **Output:**
```json
{
  "success": true,
  "data": {
    "block": {
      "id": "block_123",
      "page_id": "page_123",
      "type": "text",
      "content": "Nội dung block",
      "created_at": "2025-09-23T07:15:00.000000"
    }
  },
  "message": "Block created"
}
```

### Lấy danh sách block trong page
- **GET** `/api/block/?page_id=page_123`
- **Output:**
```json
{
  "success": true,
  "data": {
    "blocks": [
      {
        "id": "block_123",
        "page_id": "page_123",
        "type": "text",
        "content": "Nội dung block",
        "created_at": "2025-09-23T07:15:00.000000"
      }
    ]
  },
  "message": "Block list"
}
```

---

## 7. Comment

### Tạo comment
- **POST** `/api/comment/`
- **Body:**
```json
{
  "block_id": "block_123",
  "content": "Đây là comment"
}
```
- **Output:**
```json
{
  "success": true,
  "data": {
    "comment": {
      "id": "cmt_123",
      "block_id": "block_123",
      "user_id": "user_123",
      "content": "Đây là comment",
      "created_at": "2025-09-23T07:20:00.000000"
    }
  },
  "message": "Comment created"
}
```

### Lấy danh sách comment trong block
- **GET** `/api/comment/?block_id=block_123`
- **Output:**
```json
{
  "success": true,
  "data": {
    "comments": [
      {
        "id": "cmt_123",
        "block_id": "block_123",
        "user_id": "user_123",
        "content": "Đây là comment",
        "created_at": "2025-09-23T07:20:00.000000"
      }
    ]
  },
  "message": "Comment list"
}
```

---

## 8. PubSub

### Publish message
- **POST** `/api/pubsub/publish/<channel>`
- **Body:**
```json
{
  "message": "Nội dung thông báo"
}
```
- **Output:**
```json
{
  "success": true,
  "data": {
    "channel": "workspace_123",
    "message": "Nội dung thông báo"
  },
  "message": "Message published"
}
```

### Subscribe channel (WebSocket)
- **WebSocket** `/ws/pubsub/<channel>`
- **Output (server push):**
```json
{
  "channel": "workspace_123",
  "message": "Nội dung thông báo",
  "timestamp": "2025-09-23T07:30:00.000000"
}
```

---
