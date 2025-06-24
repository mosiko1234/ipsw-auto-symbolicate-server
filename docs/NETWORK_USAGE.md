# 🌐 IPSW Symbol Server - Network Usage Guide

## גישה מרחוק לשרת הסמלים

מדריך זה מיועד למפתחים שרוצים להשתמש בשרת הסמלים של IPSW ממחשבים אחרים ברשת.

---

## 📋 דרישות מוקדמות

### במחשב השרת (שם רץ השרת):
- ✅ IPSW Symbol Server פועל (Docker containers)
- ✅ פורטים פתוחים ברשת המקומית
- ✅ כתובת IP זמינה ברשת

### במחשב הקלאינט (המתחבר לשרת):
- 🐍 Python 3.7+ מותקן
- 📦 pip או pip3 זמין
- 🌐 גישה לרשת המקומית

---

## 🔧 התקנת הקלאינט

### שלב 1: הכנת קבצי הקלאינט במחשב השרת

```bash
# במחשב השרת, בתיקיית ipsw-symbol-server
cd /path/to/ipsw-symbol-server

# וודא שקבצי הקלאינט קיימים
ls -la ipsw-cli-network.py requirements-network-client.txt install-client.sh
```

### שלב 2: העברת קבצים למחשב הקלאינט

**אופציה A: העתקה ידנית**
```bash
# העתק את הקבצים הבאים למחשב הקלאינט:
- ipsw-cli-network.py
- requirements-network-client.txt  
- install-client.sh
```

**אופציה B: שיתוף ברשת**
```bash
# במחשב השרת - שתף תיקייה זמנית
python3 -m http.server 8080

# במחשב הקלאינט - הורד את הקבצים
wget http://SERVER_IP:8080/ipsw-cli-network.py
wget http://SERVER_IP:8080/requirements-network-client.txt
wget http://SERVER_IP:8080/install-client.sh
```

### שלב 3: התקנה במחשב הקלאינט

```bash
# הפעל את סקריפט ההתקנה
chmod +x install-client.sh
./install-client.sh
```

### שלב 4: הוסף לPATH (אם נדרש)

```bash
# הוסף לקובץ ~/.bashrc או ~/.zshrc
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

## 🚀 שימוש ברשת

### בדיקת חיבור לשרת

```bash
# החלף SERVER_IP בכתובת IP האמיתית של השרת
ipsw-cli-network --server http://SERVER_IP:8000 --check
```

**דוגמה:**
```bash
ipsw-cli-network --server http://10.100.102.17:8000 --check
```

### סמבליקציה בסיסית

```bash
# העלאת קובץ crash לסמבליקציה
ipsw-cli-network --server http://SERVER_IP:8000 crash.ips
```

### שימוש עם IPSW מקומי

```bash
# עבור קבצי IPSW קטנים (עד 500MB)
ipsw-cli-network --server http://SERVER_IP:8000 --local-ipsw firmware.ipsw crash.ips

# עבור קבצי IPSW גדולים (מעל 1GB) - יעבור אוטומטית למצב streaming
ipsw-cli-network --server http://SERVER_IP:8000 --local-ipsw iPhone17,3_18.5_22F76_Restore.ipsw crash.ips
```

### אפשרויות נוספות

```bash
# הצג פלט מלא (ללא קטימה)
ipsw-cli-network --server http://SERVER_IP:8000 --full crash.ips

# ללא באנר פתיחה
ipsw-cli-network --server http://SERVER_IP:8000 --no-banner crash.ips

# עזרה
ipsw-cli-network --help
```

---

## 🔗 כתובות וחיבורים

### פורטים פתוחים בשרת

| שירות | פורט | תיאור |
|--------|------|--------|
| **API Server** | `8000` | מנוע הסמבליקציה הראשי |
| **Web UI** | `80` | ממשק אינטרנט |
| **MinIO Console** | `9001` | עבור העלאת IPSW גדולים |
| **Symbol Server** | `3993` | שרת הסמלים הפנימי |
| **PostgreSQL** | `5432` | מסד נתונים |

### בדיקת חיבור מהרשת

```bash
# בדיקה עם curl
curl -s http://SERVER_IP:8000/health

# בדיקה עם telnet
telnet SERVER_IP 8000
```

---

## 🔧 פתרון בעיות

### 1. בעיות חיבור

**בעיה:** `Cannot connect to server`

**פתרונות:**
```bash
# בדוק שהשרת פועל
curl http://SERVER_IP:8000/health

# בדוק חומת אש
ping SERVER_IP

# בדוק פורטים
telnet SERVER_IP 8000
```

### 2. בעיות הרשאות

**בעיה:** `Permission denied`

**פתרון:**
```bash
# במחשב השרת - בדוק שהשירותים פועלים
docker ps | grep ipsw

# במחשב הקלאינט - בדוק הרשאות
chmod +x ~/.local/bin/ipsw-cli-network
```

### 3. קבצי IPSW גדולים

**בעיה:** `Upload timeout` או `Connection aborted`

**פתרונות:**
1. **שיטה מומלצת - MinIO Console:**
   ```bash
   # פתח דפדפן: http://SERVER_IP:9001
   # התחבר: minioadmin/minioadmin
   # העלה IPSW ל-bucket 'ipsw'
   # הרץ: ipsw-cli-network --server http://SERVER_IP:8000 crash.ips
   ```

2. **שיטה אלטרנטיבית - העתקה ידנית:**
   ```bash
   # העתק IPSW לשרת דרך USB/רשת
   # במחשב השרת: ipsw-cli --local-ipsw /path/to/ipsw crash.ips
   ```

### 4. בעיות רשת

**הגדרת Firewall במחשב השרת (macOS):**
```bash
# אפשר חיבורים נכנסים לפורט 8000
sudo pfctl -d
sudo pfctl -f /etc/pf.conf
```

**הגדרת Firewall במחשב השרת (Linux):**
```bash
# Ubuntu/Debian
sudo ufw allow 8000
sudo ufw allow 80
sudo ufw allow 9001

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

---

## 📊 דוגמאות לשימוש

### דוגמה 1: סמבליקציה מהירה

```bash
# קובץ crash בלבד
ipsw-cli-network --server http://192.168.1.100:8000 my_crash.ips
```

### דוגמה 2: IPSW קטן + crash

```bash
# IPSW קטן עם crash
ipsw-cli-network --server http://192.168.1.100:8000 \
  --local-ipsw iPhone_12_15.0_Restore.ipsw \
  crash.ips
```

### דוגמה 3: IPSW גדול (דרך MinIO)

```bash
# שלב 1: העלה IPSW דרך הדפדפן לMinIO
open http://192.168.1.100:9001

# שלב 2: הרץ סמבליקציה
ipsw-cli-network --server http://192.168.1.100:8000 crash.ips
```

---

## 🎯 טיפים לביצועים

### 1. רשת מהירה
- השתמש בחיבור Ethernet במקום WiFi
- ודא שהרשת תומכת בקצב גבוה (Gigabit+)

### 2. קבצי IPSW
- עבור קבצים גדולים (>1GB) השתמש בMinIO Console
- עבור קבצים קטנים (<500MB) השתמש בהעלאה ישירה

### 3. מקביליות
- אפשר לכמה קלאינטים לעבוד במקביל
- השרת תומך במספר חיבורים בו-זמנית

---

## 🏢 שימוש בארגון

### הגדרת שרת מרכזי
```bash
# במחשב הראשי בארגון
cd /path/to/ipsw-symbol-server
./scripts/start-server.sh

# קבל את כתובת IP
ifconfig | grep "inet " | grep -v 127.0.0.1
```

### הפצת הקלאינט לצוות
```bash
# צור package להפצה
tar -czf ipsw-client.tar.gz \
  ipsw-cli-network.py \
  requirements-network-client.txt \
  install-client.sh
```

### תיעוד לצוות
```bash
# צור הוראות פשוטות לצוות
echo "התקנה: tar -xzf ipsw-client.tar.gz && ./install-client.sh"
echo "שימוש: ipsw-cli-network --server http://COMPANY_SERVER_IP:8000 crash.ips"
```

---

## 🔒 אבטחה

### רשת מקומית בלבד
- השרת מיועד לשימוש ברשת מקומית בלבד
- אל תחשוף את השרת לאינטרנט
- השתמש בVPN עבור גישה מרחוק

### מידע רגיש
- קבצי Crash עלולים להכיל מידע רגיש
- השתמש ברשת מאובטחת
- נקה קבצים זמניים אחרי השימוש

---

## 📞 עזרה ותמיכה

### קובץ לוג שגיאות
```bash
# הפעל עם debug mode
ipsw-cli-network --server http://SERVER_IP:8000 --verbose crash.ips
```

### בדיקת סטטוס שרת
```bash
# בדיקה מפורטת
ipsw-cli-network --server http://SERVER_IP:8000 --check

# בדיקת כל השירותים במחשב השרת
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### מידע נוסף
- 📚 [README.md](README.md) - תיעוד מלא
- 🚀 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - מדריך התקנה
- 🔧 [CLI_USAGE.md](CLI_USAGE.md) - שימוש בCLI המקומי

---

**🎉 בהצלחה עם הסמבליקציה הרשתית!** 