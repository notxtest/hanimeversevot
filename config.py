import os
import logging
import random
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
LOG_FILE_NAME = "bot.log"
PORT = '5010'
OWNER_ID = int(os.getenv('OWNER_ID'))



MSG_EFFECT = [
    5104841245755180586,  # 🔥
    5107584321108051014,  # 👍
    5104858069142078462,  # 👎
    5159385139981059251,  # ❤️
    5046509860389126442,  # 🎉
    5046589136895476101,  # 💩
]

SHORT_URL = "linkshortify.com"
SHORT_API = "" 
SHORT_TUT = "https://t.me/+5qAwb0OP6-02MTdl"

# Bypass Protection
# User must stay on the Open Link page for this many seconds.
# If the user returns before this time, bypass will be detected.
BYPASS_TIME = 60

# Bot Configuration
SESSION = os.getenv('SESSION')
TOKEN = os.getenv('TOKEN')
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
WORKERS = 5

DB_URI = os.getenv('DB_URI')
DB_NAME = os.getenv('DB_NAME')

FSUBS = [[-1003921858230, True, 10]]
DB_CHANNEL = -1003903970032

AUTO_DEL = 300
ADMINS = [7171541681, 7171541681]

DISABLE_BTN = True
PROTECT = True

# Messages Configuration
MESSAGES = {
    "START": "<b>›› ʜᴇʏ!!, {first} ~ <blockquote>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴏᴜʀ ʙᴏᴛ. ɪ ᴀᴍ ʜᴇʀᴇ ᴛᴏ ʜᴇʟᴘ ʏᴏᴜ ꜰɪɴᴅ ᴀɴᴅ ɢᴇᴛ ʏᴏᴜʀ ꜰɪʟᴇs ᴇᴀsɪʟʏ ᴀɴᴅ ǫᴜɪᴄᴋʟʏ.</blockquote></b>",
    "FSUB": "<b><blockquote>›› ʜᴇʏ ×</blockquote>\n  ʏᴏᴜʀ ғɪʟᴇ ɪs ʀᴇᴀᴅʏ ‼️ ʟᴏᴏᴋs ʟɪᴋᴇ ʏᴏᴜ ʜᴀᴠᴇɴ'ᴛ sᴜʙsᴄʀɪʙᴇᴅ ᴛᴏ ᴏᴜʀ ᴄʜᴀɴɴᴇʟs ʏᴇᴛ, sᴜʙsᴄʀɪʙᴇ ɴᴏᴡ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ғɪʟᴇs</b>",
    "ABOUT": "<b>›› ᴀʙᴏᴜᴛ ᴛʜɪs ʙᴏᴛ\n\n<blockquote expandable>🤖 ʙᴏᴛ ɴᴀᴍᴇ: Fɪʟᴇ Sʜᴀʀɪɴɢ Bᴏᴛ\n👨‍💻 ᴅᴇᴠᴇʟᴏᴘᴇʀ: 🐦\n🐍 ʟᴀɴɢᴜᴀɢᴇ: <a href='https://docs.python.org/3/'>Pʏᴛʜᴏɴ 3</a>\n📚 ʟɪʙʀᴀʀʏ: <a href='https://docs.pyrogram.org/'>Pʏʀᴏɢʀᴀᴍ ᴠ2</a>\n🗄️ ᴅᴀᴛᴀʙᴀsᴇ: <a href='https://www.mongodb.com/docs/'>Mᴏɴɢᴏ ᴅʙ</a>\n\nᴛʜɪs ʙᴏᴛ ɪs ᴍᴀᴅᴇ ꜰᴏʀ ꜰɪʟᴇ sʜᴀʀɪɴɢ ᴘᴜʀᴘᴏsᴇs ᴏɴʟʏ.</blockquote></b>",
    "REPLY": "<b>For More Join - @hanime_space</b>",
    "SHORT_MSG": "<b>📊 ʜᴇʏ {first}, \n\n‼️ ɢᴇᴛ ᴀʟʟ ꜰɪʟᴇꜱ ɪɴ ᴀ ꜱɪɴɢʟᴇ ʟɪɴᴋ ‼️\n\n ⌯ ʏᴏᴜʀ ʟɪɴᴋ ɪꜱ ʀᴇᴀᴅʏ, ᴋɪɴᴅʟʏ ᴄʟɪᴄᴋ ᴏɴ ᴏᴘᴇɴ ʟɪɴᴋ ʙᴜᴛᴛᴏɴ..</b>",
    "START_PHOTO": "https://graph.org/file/b9f294b8549d8803e2bae-1a97a4394146e77a7b.jpg",
    "FSUB_PHOTO": "https://graph.org/file/b87c6c0b6ea4ff36282f6-da2c3e8dcb62211e0a.jpg",
    "SHORT_PIC": "https://graph.org/file/b9f294b8549d8803e2bae-1a97a4394146e77a7b.jpg",
    "SHORT": "https://graph.org/file/b87c6c0b6ea4ff36282f6-da2c3e8dcb62211e0a.jpg"
}

def LOGGER(name: str, client_name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    formatter = logging.Formatter(
        f"[%(asctime)s - %(levelname)s] - {client_name} - %(name)s - %(message)s",
        datefmt='%d-%b-%y %H:%M:%S'
    )
    file_handler = RotatingFileHandler(
        LOG_FILE_NAME,
        maxBytes=50_000_000,
        backupCount=10
    )
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger