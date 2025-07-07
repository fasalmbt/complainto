## Complainto

### 1. Create `.env` File

Add a `.env` file in your project root with the following content:

```
SECRET_KEY=<your-secret-key-here>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
RESET_TOKEN_EXPIRE_HOURS=1
BASE_URL=<your-url-here>
SMTP_SERVER=<your-email-server-here>
SMTP_USERNAME=<your-username-here>
SMTP_PASSWORD=<your-pass-here>
SMTP_PORT=2525
FROM_EMAIL=<your-email-here>
```

### 2. Run

```
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
python3 main.py
```

Done!


