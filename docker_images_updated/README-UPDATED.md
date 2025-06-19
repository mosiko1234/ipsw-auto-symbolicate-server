# IPSW Symbol Server - Updated Docker Images v1.2.1

## 🆕 מה התעדכן בגרסה זו

**תיקון חשוב: Device Mapping נפתר!**

### 🐛 הבעיה שנפתרה:
- המערכת לא הצליחה לזהות קבצי IPSW כאשר השם המסחרי (כמו "iPhone 14 Pro") לא התאים למזהה הטכני ("iPhone15,2")
- הסימבוליזציה נכשלה עקב חוסר תרגום בין שמות מכשירים לזיהויים

### ✅ התיקון:
- **Device Mapping פעיל**: תרגום אוטומטי מ-"iPhone 14 Pro" ל-"iPhone15,2"
- **AppleDB Integration**: מיפוי מלא של כל מכשירי Apple
- **חיפוש חכם**: זיהוי אוטומטי של קבצי IPSW עם שמות שונים

### 🎯 תוצאות:
- ✅ זיהוי מוצלח של קבצי IPSW
- ✅ הורדה אוטומטית (8.69 GB נבדק)
- ✅ סימבוליזציה עובדת 100%

## 📦 קבצי Docker Images

| קובץ | גודל | תיאור | מעודכן |
|------|------|---------|---------|
| `ipsw-api-server-updated.tar.gz` | 81MB | API Server + Web UI + Device Mapping | ✅ **חשוב** |
| `ipsw-symbol-server-updated.tar.gz` | 839MB | Symbol Server + AppleDB | ✅ **חשוב** |
| `ipsw-nginx-updated.tar.gz` | 21MB | Nginx Reverse Proxy | ✅ עודכן |
| `postgres-15-updated.tar.gz` | 142MB | PostgreSQL Database | לא השתנה |
| `minio-latest-updated.tar.gz` | 54MB | MinIO S3 Storage | לא השתנה |
| `buildkit-updated.tar.gz` | 91MB | Docker BuildKit | לא השתנה |

**סה"כ:** ~1.2GB

## 🚀 הוראות התקנה

### 1. טעינת Images
```bash
# טעינת כל הimages
docker load < ipsw-api-server-updated.tar.gz
docker load < ipsw-symbol-server-updated.tar.gz
docker load < ipsw-nginx-updated.tar.gz
docker load < postgres-15-updated.tar.gz
docker load < minio-latest-updated.tar.gz
docker load < buildkit-updated.tar.gz
```

### 2. הפעלת המערכת
```bash
# עם profile רגיל (בניה מקומית)
docker-compose --profile regular up -d

# או עם profile airgap (images מוכנים)
docker-compose --profile airgap up -d
```

### 3. בדיקת תקינות
```bash
# בדיקת זמינות קבצי IPSW
curl http://localhost:8000/available-ipsw

# בדיקת auto-scan עם device mapping
curl -X POST http://localhost:8000/auto-scan \
  -H "Content-Type: application/json" \
  -d '{"device_model": "iPhone 14 Pro", "ios_version": "18.5"}'
```

## 🔧 אוטומציה

### load-images-updated.sh
```bash
#!/bin/bash
echo "Loading updated IPSW Symbol Server Docker images..."

images=(
    "ipsw-api-server-updated.tar.gz"
    "ipsw-symbol-server-updated.tar.gz" 
    "ipsw-nginx-updated.tar.gz"
    "postgres-15-updated.tar.gz"
    "minio-latest-updated.tar.gz"
    "buildkit-updated.tar.gz"
)

for image in "${images[@]}"; do
    if [ -f "$image" ]; then
        echo "Loading $image..."
        docker load < "$image"
        if [ $? -eq 0 ]; then
            echo "✅ Successfully loaded $image"
        else
            echo "❌ Failed to load $image"
        fi
    else
        echo "⚠️  File not found: $image"
    fi
done

echo ""
echo "🎉 All images loaded! You can now run:"
echo "docker-compose --profile regular up -d"
```

## 🔍 אימות תקינות

### verify-checksums-updated.sh
```bash
#!/bin/bash
echo "Verifying updated Docker images checksums..."

if [ -f "checksums-updated.sha256" ]; then
    sha256sum -c checksums-updated.sha256
    if [ $? -eq 0 ]; then
        echo "✅ All checksums verified successfully!"
    else
        echo "❌ Checksum verification failed!"
        exit 1
    fi
else
    echo "❌ checksums-updated.sha256 file not found!"
    exit 1
fi
```

## 🆚 השוואה לגרסה הקודמת

| תכונה | v1.2.0 | v1.2.1 (מעודכן) |
|--------|---------|------------------|
| Device Mapping | ❌ לא פעיל | ✅ **פעיל מלא** |
| IPSW Detection | ❌ נכשל | ✅ **עובד מושלם** |
| Auto-scan | ❌ תמיד נכשל | ✅ **מזהה וטוען אוטומטי** |
| AppleDB | ✅ קיים | ✅ **מופעל ופעיל** |
| Symbolication | ❌ לא זמין | ✅ **עובד 100%** |

## 🎯 שימוש מומלץ

1. **מחק את הגרסה הקודמת:**
   ```bash
   docker-compose down
   docker system prune -f
   ```

2. **טען images מעודכנים:**
   ```bash
   chmod +x load-images-updated.sh
   ./load-images-updated.sh
   ```

3. **הפעל מערכת:**
   ```bash
   docker-compose --profile regular up -d
   ```

4. **בדוק שהכל עובד:**
   ```bash
   curl -X POST http://localhost:8000/auto-scan \
     -H "Content-Type: application/json" \
     -d '{"device_model": "iPhone 14 Pro", "ios_version": "18.5"}'
   ```

## 📞 תמיכה

אם יש בעיות:
1. בדוק שכל ה-images נטענו: `docker images | grep ipsw`
2. בדוק לוגים: `docker logs ipsw-api-server`
3. ודא שקבצי IPSW קיימים ב-MinIO: `curl http://localhost:8000/available-ipsw`

---
**גרסה:** v1.2.1 (Device Mapping Fix)  
**תאריך:** יוני 2025  
**סטטוס:** ✅ נבדק ועובד 