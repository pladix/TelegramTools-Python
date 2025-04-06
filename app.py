# Telegram Tools - Python
# Copyright (c) 2025 @PladixOficial
# Todos os direitos reservados

import sqlite3
from pyrogram import Client
from pyrogram.errors import FloodWait, RPCError
import asyncio
from datetime import datetime
import os

def setup_database():
    conn = sqlite3.connect('telegram_accounts.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS accounts
                 (id INTEGER PRIMARY KEY, phone TEXT UNIQUE, api_id TEXT, api_hash TEXT, 
                  session_file TEXT, added_date TEXT)''')
    conn.commit()
    conn.close()

async def add_new_account():
    phone = input("")
    api_id = input("")
    api_hash = input("")
    session_file = f"sessions/{phone}"
    
    client = Client(session_file, api_id=api_id, api_hash=api_hash, phone_number=phone)
    await client.connect()
    
    if not await client.is_user_authorized():
        sent_code = await client.send_code(phone)
        code = input("")
        await client.sign_in(phone, sent_code.phone_code_hash, code)
    
    conn = sqlite3.connect('telegram_accounts.db')
    c = conn.cursor()
    c.execute("INSERT INTO accounts (phone, api_id, api_hash, session_file, added_date) VALUES (?, ?, ?, ?, ?)",
              (phone, api_id, api_hash, session_file, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    
    await client.disconnect()

def list_accounts():
    conn = sqlite3.connect('telegram_accounts.db')
    c = conn.cursor()
    c.execute("SELECT phone, added_date FROM accounts")
    accounts = c.fetchall()
    conn.close()
    
    if accounts:
        for i, (phone, date) in enumerate(accounts, 1):
            print(f"{i}. {phone} - {date}")

async def connect_all_accounts():
    conn = sqlite3.connect('telegram_accounts.db')
    c = conn.cursor()
    c.execute("SELECT phone, api_id, api_hash, session_file FROM accounts")
    accounts = c.fetchall()
    conn.close()
    
    clients = []
    for phone, api_id, api_hash, session_file in accounts:
        client = Client(session_file, api_id=api_id, api_hash=api_hash, phone_number=phone)
        await client.connect()
        if await client.is_user_authorized():
            clients.append((phone, client))
        else:
            await client.disconnect()
    
    return clients

async def mass_join_group():
    link = input("")
    clients = await connect_all_accounts()
    
    for phone, client in clients:
        try:
            await client.join_chat(link)
        except FloodWait as e:
            await asyncio.sleep(e.x)
        except RPCError:
            pass
        finally:
            await client.disconnect()

async def mass_report_group():
    link = input("")
    message_id = int(input(""))
    reason = input("").lower()
    
    clients = await connect_all_accounts()
    
    for phone, client in clients:
        try:
            if message_id > 0:
                await client.report(chat_id=link, message_ids=[message_id], reason="spam" if reason == "spam" else "other", description=f"{reason}")
            else:
                await client.report(chat_id=link, reason="spam" if reason == "spam" else "other", description=f"{reason}")
        except FloodWait as e:
            await asyncio.sleep(e.x)
        except RPCError:
            pass
        finally:
            await client.disconnect()

async def mass_report_user():
    target = input("")
    reason = input("").lower()
    
    clients = await connect_all_accounts()
    
    for phone, client in clients:
        try:
            await client.report(user_id=target, reason="spam" if reason == "spam" else "other", description=f"{reason}")
        except FloodWait as e:
            await asyncio.sleep(e.x)
        except RPCError:
            pass
        finally:
            await client.disconnect()

async def loop_report(option):
    while True:
        if option == "4":
            await mass_report_group()
        elif option == "5":
            await mass_report_user()
        
        cont = input("").lower()
        if cont != "s":
            break

async def main_menu():
    if not os.path.exists("sessions"):
        os.makedirs("sessions")
    setup_database()
    
    while True:
        choice = input("")
        
        if choice == "1":
            await add_new_account()
        elif choice == "2":
            list_accounts()
        elif choice == "3":
            await mass_join_group()
        elif choice == "4":
            await loop_report("4")
        elif choice == "5":
            await loop_report("5")
        elif choice == "0":
            break

if __name__ == "__main__":
    asyncio.run(main_menu())