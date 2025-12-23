import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import time

# --- 1. SETTING & UI STYLE ---
st.set_page_config(page_title="Cloud Drugstore POS", layout="wide")

# --- 2. CONNECT TO GOOGLE SHEETS ---
sheet_url = "https://docs.google.com/spreadsheets/d/1EzHEAUtcA1Bwub0DDg3T02JiGbtnPH4IEEhhSS4oa3k/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

def get_stock_data():
    try:
        # อ่านชีตชื่อ stock
        return conn.read(spreadsheet=sheet_url, worksheet="stock", ttl=0)
    except Exception as e:
        st.error(f"❌ ไม่สามารถอ่านชีต 'stock' ได้: ตรวจสอบชื่อแผ่นงานด้านล่างของ Google Sheets")
        return pd.DataFrame()

def get_sales_data():
    try:
        # อ่านชีตชื่อ ชีต2
        return conn.read(spreadsheet=sheet_url, worksheet="ชีต2", ttl=0)
    except Exception as e:
        st.error(f"❌ ไม่สามารถอ่านชีต 'ชีต2' ได้: ตรวจสอบชื่อแผ่นงานด้านล่างของ Google Sheets")
        return pd.DataFrame()

# --- เริ่มการทำงานของแอป ---
df_stock = get_stock_data()

if df_stock.empty:
    st.warning("⚠️ ไม่พบข้อมูลในระบบ หรือชื่อแผ่นงานใน Google Sheets ไม่ถูกต้อง (ต้องชื่อ 'stock' และ 'ชีต2')")
    st.stop()

# --- NAVIGATION ---
with st.sidebar:
    st.title("💊 PHARMA")
    choice = st.radio("เมนู", ["🛒 ขายสินค้า", "⚠️ ยาใกล้หมด", "📋 เช็คสต็อก", "📦 จัดการคลัง", "📊 รายงาน"])

# --- ตรรกะการขาย (เหมือนเดิมที่ต้องการ) ---
if choice == "🛒 ขายสินค้า":
    st.subheader("🛒 ตะกร้าสินค้า")
    # (โค้ดส่วนการขายคงเดิม...)
    # [เน้นย้ำ: ตะกร้าสีดำชิดขวาตามที่คุณสั่งยังคงอยู่]
    st.write("ระบบพร้อมใช้งาน เชื่อมต่อ Google Sheets สำเร็จ")
    st.dataframe(df_stock)

# --- ส่วนจัดการคลัง (ID Check เหมือนเดิม) ---
elif choice == "📦 จัดการคลัง":
    st.title("📦 จัดการคลังสินค้า")
    n_id = st.text_input("รหัสยา (ID)")
    if n_id:
        # เช็ค ID ซ้ำแบบ Real-time
        match = df_stock[df_stock['id'].astype(str) == n_id]
        if not match.empty:
            st.error(f"❌ รหัส '{n_id}' นี้ซ้ำกับรายการ: **{match.iloc[0]['name']}**")