import firebase_admin
from firebase_admin import credentials, firestore

KEY_PATH = "firestore/firebase-adminsdk.json"
BUCKET_NAME = "du-do-zi.firebasestorage.app"

def init_firebase():    # SDK 초기화
    if not firebase_admin._apps:
        cred = credentials.Certificate(KEY_PATH)
        firebase_admin.initialize_app(cred, {"storageBucket": BUCKET_NAME})

def get_db():   # 이거 호출하면 어디서든 DB 접근 가능
    init_firebase()
    return firestore.client()