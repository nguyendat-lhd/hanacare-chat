# 📜 Scripts Utilities

Các script tiện ích để quản lý MongoDB và users.

## 🔧 Scripts Available

### 1. `check_mongodb.py` - Kiểm tra kết nối MongoDB
```bash
python scripts/check_mongodb.py
```

### 2. `seed_users.py` - Tạo users mẫu
```bash
python scripts/seed_users.py
```

### 3. `delete_user.py` - Xóa user
```bash
python scripts/delete_user.py <user_id>
python scripts/delete_user.py --list  # Xem danh sách users
```

### 4. `reset_db.py` - Reset toàn bộ database
```bash
python scripts/reset_db.py
```

## ⚠️ Lưu ý về MongoDB Authentication

Nếu MongoDB yêu cầu authentication, bạn có 2 lựa chọn:

### Option A: Tạo MongoDB mới không có auth (Development)

```bash
# Dừng MongoDB hiện tại
brew services stop mongodb-community
# hoặc
docker stop mongodb

# Tạo MongoDB mới không có auth
docker run -d -p 27017:27017 --name mongodb-dev mongo:latest

# Cập nhật .env
# MONGODB_URI=mongodb://localhost:27017
```

### Option B: Thêm credentials vào .env

```bash
# Sửa .env
MONGODB_URI=mongodb://username:password@localhost:27017/
```

## 📋 Users mẫu được tạo

Sau khi chạy `seed_users.py`, bạn sẽ có các users sau:

| User ID | Password | Email |
|---------|----------|-------|
| admin | admin123 | admin@healthsync.ai |
| testuser | test123 | test@example.com |
| demo | demo123 | demo@healthsync.ai |
| user1 | password123 | user1@example.com |

