import hashlib
import os
import sqlite3
from typing import Optional

from database.db_manager import get_connection


def _hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    if salt is None:
        salt = os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), 100_000)
    return dk.hex(), salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    test_hash, _ = _hash_password(password, salt)
    return test_hash == stored_hash


def ensure_default_users() -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM utilisateurs')
    total = cursor.fetchone()[0]
    if total == 0:
        pwd_hash, salt = _hash_password('admin')
        cursor.execute(
            'INSERT INTO utilisateurs (username, password_hash, salt, role) VALUES (?, ?, ?, ?)',
            ('admin', pwd_hash, salt, 'admin')
        )
        pwd_hash, salt = _hash_password('operateur')
        cursor.execute(
            'INSERT INTO utilisateurs (username, password_hash, salt, role) VALUES (?, ?, ?, ?)',
            ('operateur', pwd_hash, salt, 'operateur')
        )
    conn.commit()
    conn.close()


def authenticate(username: str, password: str) -> Optional[dict]:
    username = (username or '').strip()
    if not username:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM utilisateurs WHERE username = ?', (username.lower(),))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    if verify_password(password, row['password_hash'], row['salt']):
        return {
            'id': row['id'],
            'username': row['username'],
            'role': row['role'],
        }
    return None


def create_user(username: str, password: str, role: str = 'operateur') -> dict:
    username = username.strip().lower()
    if not username:
        raise ValueError('Le nom d’utilisateur est requis.')
    if len(password) < 3:
        raise ValueError('Le mot de passe doit contenir au moins 3 caractères.')
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM utilisateurs WHERE username = ?', (username,))
    if cursor.fetchone():
        conn.close()
        raise ValueError('Cet utilisateur existe déjà.')
    pwd_hash, salt = _hash_password(password)
    cursor.execute(
        'INSERT INTO utilisateurs (username, password_hash, salt, role) VALUES (?, ?, ?, ?)',
        (username, pwd_hash, salt, role)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {'id': user_id, 'username': username, 'role': role}


def list_users() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, role FROM utilisateurs ORDER BY username')
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows
