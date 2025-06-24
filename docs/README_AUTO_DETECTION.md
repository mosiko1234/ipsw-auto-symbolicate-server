# IPSW Auto-Detection System

## תיקון הבעיות שהיו במערכת

### הבעיות שתוקנו:

1. **Cache Sync בעיות** - Symbol server לא התעדכן אוטומטית כשהעליתם קבצי IPSW חדשים
2. **Manual Refresh נדרש** - צריך היה לעשות restart/refresh ידני אחרי כל IPSW חדש  
3. **Auto-Scan ידני** - צריך היה להריץ auto-scan בעצמכם לכל device/version חדש

### הפתרון החדש:

המערכת עכשיו כוללת **S3 File Watcher** שמזהה אוטומטית קבצים חדשים ומפעיל את כל התהליך!

## איך זה עובד עכשיו

### 1. הרצה עם Auto-Detection
```bash
# התחילו את המערכת כרגיל
docker-compose up -d

# ה-File Watcher יתחיל אוטומטית ויבדוק כל 5 דקות
```

### 2. העלאת IPSW חדש
```bash
# פשוט העלו קובץ ל-S3 באמצעות MinIO UI או CLI
# לדוגמה: iPhone16,1_18.5_22F76_Restore.ipsw

# המערכת תזהה אוטומטית תוך 5 דקות ותעשה:
# 1. Cache refresh ב-Symbol Server
# 2. Auto-scan עבור הdevice/version החדש  
# 3. יצירת symbols אוטומטית
```

### 3. ביקורת ומעקב
```bash
# בדיקת סטטוס File Watcher
curl http://localhost:8000/file-watcher/status | jq '.'

# בדיקת קבצי IPSW זמינים
curl http://localhost:8000/available-ipsw | jq '.files[] | {device, version, build}'

# בדיקת symbols זמינים
curl http://localhost:3993/v1/ipsws | jq '.'
```

## API Endpoints החדשים

### File Watcher Management
```bash
# סטטוס File Watcher
GET /file-watcher/status

# הפעלה מחדש של File Watcher
POST /file-watcher/restart

# רענון cache ידני (עדיין זמין כ-fallback)
POST /refresh-cache
```

### תגובה דוגמה לסטטוס File Watcher:
```json
{
  "success": true,
  "watcher": {
    "running": true,
    "last_check": "2025-06-20T21:45:30",
    "known_files_count": 3,
    "check_interval_seconds": 300,
    "auto_scan_cooldown_minutes": 10,
    "recent_auto_scans": {
      "iPhone17,3_18.5_22F76": "2025-06-20T21:39:45"
    }
  }
}
```

## הגדרות מתקדמות

### התאמת תדירות בדיקה
```bash
# במשתני הסביבה של docker-compose.yml
environment:
  - S3_CHECK_INTERVAL=300  # בדיקה כל 5 דקות (default)
  - AUTO_SCAN_COOLDOWN=600 # 10 דקות המתנה בין auto-scans לאותו device
```

### Rate Limiting
המערכת כוללת הגנה מפני עומס:
- **Auto-scan cooldown**: 10 דקות בין סריקות לאותו device/version
- **Background processing**: File Watcher פועל ברקע ולא חוסם פעולות אחרות
- **Error recovery**: התאוששות אוטומטית מכשלונות

## Workflow מומלץ למפתחים

### תהליך העבודה הנכון:
```bash
# 1. העלאת IPSW חדש לS3
# (דרך MinIO UI: http://localhost:9001)

# 2. המתנה 5 דקות (או הפעלת refresh ידני)
curl -X POST http://localhost:8000/refresh-cache

# 3. בדיקה שהקובץ זוהה
curl http://localhost:8000/available-ipsw | jq '.files[-1]'

# 4. וידוא שsymbols נוצרו (אוטומטית)
curl http://localhost:3993/v1/ipsws | jq '.ipsws[] | select(.device=="iPhone17,3")'

# 5. בדיקת simbolication
ipsw symbolicate --server "http://localhost:3993" crash_file.ips
```

### אם משהו לא עובד:
```bash
# 1. בדיקת בריאות המערכת
curl http://localhost:8000/health
curl http://localhost:3993/health

# 2. בדיקת File Watcher
curl http://localhost:8000/file-watcher/status

# 3. הפעלה מחדש של File Watcher
curl -X POST http://localhost:8000/file-watcher/restart

# 4. refresh ידני כ-fallback
curl -X POST http://localhost:8000/refresh-cache

# 5. auto-scan ידני במקרה קיצון
curl -X POST "http://localhost:3993/v1/auto-scan?device_model=iPhone17,3&ios_version=18.5&build_number=22F76"
```

## מעקב ו-Debug

### לוגים חשובים לבדיקה:
```bash
# File Watcher logs
docker logs ipsw-api-server | grep "file watcher\|S3.*detected"

# Symbol Server auto-scan logs  
docker logs ipsw-symbol-server | grep "auto-scan\|Successfully auto-scanned"

# S3 Manager logs
docker logs ipsw-api-server | grep "S3.*refresh\|Cached.*IPSW"
```

### דוגמאות ללוגים תקינים:
```
2025-06-20 21:39:45 - INFO - S3 file watcher started
2025-06-20 21:40:15 - INFO - Detected 1 new files and 0 changed files  
2025-06-20 21:40:16 - INFO - Processing new/changed IPSW: iPhone17,3_18.5_22F76_Restore.ipsw
2025-06-20 21:40:21 - INFO - Successfully triggered symbol server cache refresh
2025-06-20 21:40:35 - INFO - Auto-scan completed: Successfully auto-scanned and cached 25211 symbols
```

## התאמה לסביבות שונות

### Production Environment
```yaml
# docker-compose.yml
environment:
  - S3_CHECK_INTERVAL=180      # בדיקה כל 3 דקות בproduction
  - AUTO_SCAN_COOLDOWN=300     # 5 דקות cooldown בproduction
  - CACHE_SIZE_GB=200          # cache גדול יותר
```

### Development Environment  
```yaml
environment:
  - S3_CHECK_INTERVAL=60       # בדיקה כל דקה לפיתוח
  - AUTO_SCAN_COOLDOWN=120     # 2 דקות cooldown לפיתוח
```

## יתרונות החדשים

✅ **Zero Manual Intervention** - העלתם IPSW → המערכת מטפלת בהכל  
✅ **Real-time Detection** - זיהוי תוך 5 דקות  
✅ **Automatic Symbol Generation** - auto-scan אוטומטי  
✅ **Rate Limiting** - הגנה מפני עומס  
✅ **Error Recovery** - התאוששות אוטומטית  
✅ **Backward Compatibility** - refresh ידני עדיין עובד  
✅ **Developer Friendly** - APIs לניטור ובקרה  

המערכת עכשיו עובדת כמו שרצית מלכתחילה - **Upload & Forget**! 🎉 