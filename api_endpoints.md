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

### Đăng nhập
- **POST** `/api/auth/login`
- **Body:**
```json
{
  "email": "abc@13579.com",
  "password": "132442"
}
```

### Đăng xuất
- **POST** `/api/auth/logout`
- **Header:** `Authorization: Bearer <access_token>`

### Làm mới token
- **POST** `/api/auth/refresh`
- **Header:** `Authorization: Bearer <access_token>`

### Lấy thông tin user hiện tại
- **GET** `/api/auth/me`
- **Header:** `Authorization: Bearer <access_token>`

---

## 2. User

### Lấy profile
- **GET** `/api/user/profile`
- **Header:** `Authorization: Bearer <access_token>`

### Cập nhật profile
- **PUT** `/api/user/profile`
- **Header:** `Authorization: Bearer <access_token>`
- **Body:**
```json
{
  "full_name": "Tên mới",
  "username": "username_moi",
  "language": "vi",
  "timezone": "Asia/Ho_Chi_Minh"
}
```

### Lấy settings
- **GET** `/api/user/settings`
- **Header:** `Authorization: Bearer <access_token>`

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

### Đổi mật khẩu
- **POST** `/api/user/change-password`
- **Header:** `Authorization: Bearer <access_token>`
- **Body:**
```json
{
  "old_password": "132442",
  "new_password": "matkhaumoi123"
}
```

### Lấy workspace của user
- **GET** `/api/user/workspaces`
- **Header:** `Authorization: Bearer <access_token>`

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

*Bạn có thể yêu cầu thêm các endpoint khác (Page, Block, Comment, PubSub) nếu cần chi tiết hơn!*
