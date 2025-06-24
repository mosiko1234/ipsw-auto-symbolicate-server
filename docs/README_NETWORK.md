# 🌐 IPSW Symbol Server - גישה רשתית

## תשובה לשאלה: "ואם אני פונה ממחשב אחר? זה יעבוד?"

**כן! השרת כבר מוכן לגישה רשתית.** השרת שלך פועל על הכתובת `10.100.102.17` ונגיש לכל המחשבים ברשת המקומית.

---

## 🚀 גישה מיידית

### מבדיקת הדפדפן (הקל ביותר)
פתח דפדפן במחשב אחר וגש לכתובת:
```
http://10.100.102.17
```

### מבדיקת CLI (ללא התקנה)
```bash
# בדיקה מהירה
curl http://10.100.102.17:8000/health
```

---

## 📥 התקנת CLI למחשבים אחרים

### שלב 1: הורד את קבצי הקלאינט
```bash
# אופציה A: הורד מהשרת
wget http://10.100.102.17:8080/ipsw-network-client-v1.2.5.tar.gz

# אופציה B: העתק קבצים
# העתק את ipsw-network-client-v1.2.5.tar.gz למחשב המטרה
```

### שלב 2: התקנה
```bash
# חלץ ותתקן
tar -xzf ipsw-network-client-v1.2.5.tar.gz
cd ipsw-network-client-v1.2.5
./install-client.sh
```

### שלב 3: הוסף לPATH
```bash
# הוסף לקובץ ה-shell שלך
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

## 🎯 שימוש מרחוק

### סמבליקציה בסיסית
```bash
ipsw-cli-network --server http://10.100.102.17:8000 crash.ips
```

### עם IPSW מקומי (קטן)
```bash
ipsw-cli-network --server http://10.100.102.17:8000 --local-ipsw firmware.ipsw crash.ips
```

### עם IPSW גדול
```bash
# שלב 1: העלה דרך MinIO Console
open http://10.100.102.17:9001
# התחבר: minioadmin/minioadmin
# העלה ל-bucket 'ipsw'

# שלב 2: הרץ סמבליקציה
ipsw-cli-network --server http://10.100.102.17:8000 crash.ips
```

---

## 🔗 כל השירותים הזמינים ברשת

| שירות | כתובת | תיאור |
|--------|--------|--------|
| **Web UI** | http://10.100.102.17 | ממשק אינטרנט מלא |
| **API** | http://10.100.102.17:8000 | CLI ו-API calls |
| **MinIO Console** | http://10.100.102.17:9001 | העלאת קבצי IPSW גדולים |

---

## ⚡ בדיקה מהירה

```bash
# בדוק שהשרת נגיש
curl http://10.100.102.17:8000/health

# אם עובד - תראה:
{"status":"healthy","timestamp":"2025-06-22T15:53:22.868645"}
```

---

## 🏢 לשימוש בצוות

### הפץ לכל הצוות
1. שתף את הקובץ: `ipsw-network-client-v1.2.5.tar.gz`
2. תן להם את ההוראות:
   ```bash
   tar -xzf ipsw-network-client-v1.2.5.tar.gz
   ./install-client.sh
   ```
3. כל אחד יוכל להשתמש עם:
   ```bash
   ipsw-cli-network --server http://10.100.102.17:8000 crash.ips
   ```

---

## 🔧 פתרון בעיות

### אם אין חיבור
```bash
# בדוק רשת
ping 10.100.102.17

# בדוק פורט
telnet 10.100.102.17 8000
```

### אם יש בעיות חומת אש
במחשב השרת (macOS):
```bash
# השבת חומת אש זמנית לבדיקה
sudo pfctl -d
```

---

## 📋 סיכום

✅ **השרת כבר נגיש ברשת**: `10.100.102.17`  
✅ **Web UI עובד**: פתח דפדפן ולך ל-http://10.100.102.17  
✅ **CLI זמין**: התקן את `ipsw-network-client-v1.2.5.tar.gz`  
✅ **תומך בקבצים גדולים**: דרך MinIO Console  
✅ **מספר משתמשים במקביל**: כל הצוות יכול להשתמש בו-זמנית  

**בקצרה: כן, זה יעבוד ממחשבים אחרים ברשת! 🎉** 