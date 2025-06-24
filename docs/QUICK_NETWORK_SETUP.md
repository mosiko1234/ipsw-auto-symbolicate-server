# 🚀 הגדרה מהירה לרשת - IPSW Symbol Server

## שלבים מהירים למחשב חדש ברשת

### 1. בדיקה מהירה (ללא התקנה)
```bash
# בדוק שהשרת נגיש
curl http://10.100.102.17:8000/health

# אמור לראות: {"status":"healthy",...}
```

### 2. בדפדפן (הכי פשוט)
פתח: **http://10.100.102.17**

### 3. CLI מהיר (מתקדמים)

```bash
# הורד package
wget http://10.100.102.17:8080/ipsw-network-client-v1.2.5-updated.tar.gz

# או העתק מUSB/רשת
scp user@server:/path/ipsw-network-client-v1.2.5-updated.tar.gz .

# חלץ
tar -xzf ipsw-network-client-v1.2.5-updated.tar.gz

# שימוש מיידי (ללא התקנה)
./network-cli --check
./network-cli crash.ips
./network-cli --local-ipsw firmware.ipsw crash.ips
```

### 4. התקנה קבועה (אופציונלי)
```bash
./install-client.sh
# אז: ipsw-cli-network --server http://10.100.102.17:8000 crash.ips
```

---

## דוגמאות מהירות

### סמבליקציה בסיסית
```bash
./network-cli crash.ips
```

### עם IPSW מקומי
```bash
./network-cli --local-ipsw firmware.ipsw crash.ips
```

### בדיקת שרת
```bash
./network-cli --check
```

### שרת אחר
```bash
./network-cli --server http://192.168.1.100:8000 crash.ips
```

---

## כל הכתובות השימושיות

- **Web UI**: http://10.100.102.17
- **API**: http://10.100.102.17:8000  
- **MinIO**: http://10.100.102.17:9001

---

**זהו! פשוט וקל לשימוש** 🎉 