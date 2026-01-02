import os
from django.conf import settings
import firebase_admin
from firebase_admin import credentials, auth, storage, firestore


def initialize():
    if firebase_admin._apps:
        return

    cred_path = getattr(settings, 'FIREBASE_SERVICE_ACCOUNT_PATH', None) or os.environ.get('FIREBASE_SERVICE_ACCOUNT_PATH') or os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if not cred_path:
        return

    options = {}
    bucket = getattr(settings, 'FIREBASE_STORAGE_BUCKET', None) or os.environ.get('FIREBASE_STORAGE_BUCKET')
    if bucket:
        options['storageBucket'] = bucket

    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, options or None)


def verify_id_token(id_token):
    return auth.verify_id_token(id_token)


def get_auth():
    return auth


def get_storage_bucket():
    return storage.bucket()


def get_firestore_client():
    return firestore.client()
