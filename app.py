import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- 1. SETTING & UI STYLE ---
st.set_page_config(page_title="Cloud Drugstore POS", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; background-color: #1A202C !important; color: #E2E8F0 !important; }
    
    /* ตะกร้าสินค้า: ตัวหนังสือสีดำ พื้นสีขาว ชิดขวา */
    .cart-row-container {
        background-color: #FFFFFF !important;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 10px;
        border: 1px solid #CBD5E0;
        text-align: right;
    }
    .cart-item-name { font-weight: 800 !important; color: #000000 !important; font-size: 1.1rem; }
    .cart-qty-num { color: #000000 !important; font-weight: 800 !important; font-size: 1.3rem; }
    .cart-price-sub { color: #4A5568 !important; font-size: 0.85rem; font-weight: 600; }

    .low-stock-card { background-color: #822727 !important; border: 2px solid #FC8181; padding: 20px; border-radius: 12px; margin-bottom: 15px; color: white !important; }
    .admin-card { background-color: #2D3748; padding: 25px; border-radius: 12px; border: 1px solid #4A5568; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# --- 2. CONNECT TO GOOGLE SHEETS (DIRECT METHOD) ---
# ลิงก์จากไฟล์ "คลังยาออนไลน์" ของคุณ
SHEET_URL = "https://docs.google.com/spreadsheets/d/1EzHEAUtcA1Bwub0DDg3T02JiGbtnPH4IEEhhSS4oa3k/edit?usp=sharing"

def load_data(sheet_name):
    # เปลี่ยนลิงก์ให้เป็นแบบ Export CSV เพื่อให้อ่านง่ายและไม่ติดสิทธิ์
    csv_url = SHEET_URL.replace('/edit?usp=sharing', f'/gviz/tq?tqx=out:csv&sheet={sheet_name}')
    try:
        return pd.read_csv(csv_url)
    except Exception as e:
        st.error(f"ไม่สามารถอ่านแผ่นงาน '{sheet_name}' ได้: {e}")
        return pd.DataFrame()

# ดึงข้อมูลเริ่มต้น
df_stock = load_data("stock")
df_sales = load_data("ชีต2")

# ตรวจสอบว่ามีข้อมูลพื้นฐานไหม
if df_stock.empty:
    st.warning("⚠️ ไม่พบข้อมูลในแผ่นงาน 'stock' หรือลิงก์อาจมีปัญหา")
    st.stop()

# --- 3. MAIN NAVIGATION ---
with st.sidebar:
    st.markdown("<h1 style='color: #63B3ED; text-align: center;'>💊 PHARMA</h1>", unsafe_allow_html=True)
    choice = st.radio("เลือกรายการ", ["🛒 ขายสินค้า", "📋 รายการสินค้า", "📦 จัดการคลัง", "📊 รายงาน"])

# --- 4. SALES INTERFACE ---
if choice == "🛒 ขายสินค้า":
    if 'cart' not in st.session_state: st.session_state.cart = {}
    
    col_left, col_right = st.columns([1, 1.2])
    
    with col_left:
        st.subheader("🔍 เลือกสินค้า")
        search = st.text_input("ค้นหาชื่อยาหรือยิงบาร์โค้ด")
        
        items = df_stock[df_stock['qty'] > 0]
        options = ["-- เลือกรายการ --"] + [f"{r['name']} (คงเหลือ {r['qty']})" for _, r in items.iterrows()]
        
        # ค้นหาตำแหน่งยาให้อัตโนมัติ (ID Check Real-time)
        found_idx = 0
        if search:
            for i, opt in enumerate(options):
                if search.lower() in opt.lower():
                    found_idx = i
                    break
        
        selected = st.selectbox("รายการสินค้า", options, index=found_idx)
        
        if selected != "-- เลือกรายการ --":
            name_only = selected.split(" (")[0]
            item_data = df_stock[df_stock['name'] == name_only].iloc[0]
            st.info(f"💰 ราคา: {item_data['price']} บาท | รหัส: {item_data['id']}")
            
            if st.button("➕ เพิ่มเข้าตะกร้า", use_container_width=True, type="primary"):
                s_id = str(item_data['id'])
                if s_id in st.session_state.cart:
                    if st.session_state.cart[s_id]['qty'] < item_data['qty']:
                        st.session_state.cart[s_id]['qty'] += 1
                else:
                    st.session_state.cart[s_id] = {'name': item_data['name'], 'price': item_data['price'], 'qty': 1, 'max': item_data['qty']}
                st.rerun()

    with col_right:
        st.subheader("🛒 รายการรอชำระเงิน")
        if not st.session_state.cart:
            st.info("ยังไม่มีสินค้าในตะกร้า")
        else:
            grand_total = 0
            for tid, info in list(st.session_state.cart.items()):
                subtotal = info['qty'] * info['price']
                grand_total += subtotal
                
                # ตะกร้าดีไซน์ชิดขวา ตัวหนังสือสีดำ
                st.markdown(f'''
                <div class="cart-row-container">
                    <div class="cart-item-name">{info['name']}</div>
                    <div class="cart-price-sub">฿{info['price']} x {info['qty']} = ฿{subtotal}</div>
                </div>
                ''', unsafe_allow_html=True)
                
                # ปุ่มลบแบบเล็ก
                if st.button(f"ยกเลิก {info['name']}", key=f"del_{tid}"):
                    del st.session_state.cart[tid]
                    st.rerun()
            
            st.markdown(f"<h2 style='text-align: right; color: #63B3ED;'>รวมทั้งสิ้น ฿{grand_total:,.2f}</h2>", unsafe_allow_html=True)
            st.warning("⚠️ การบันทึกข้อมูลถาวรจำเป็นต้องตั้งค่า Google Sheets API เพิ่มเติม ปัจจุบันระบบจำลองการขายได้เท่านั้น")

# --- 5. STOCK LIST ---
elif choice == "📋 รายการสินค้า":
    st.subheader("📋 สินค้าคงคลังทั้งหมด (จาก Google Sheets)")
    st.dataframe(df_stock, use_container_width=True, hide_index=True)
    
    # ยาใกล้หมด
    low_stock = df_stock[df_stock['qty'] <= 2]
    if not low_stock.empty:
        st.error("⚠️ รายการยาที่ใกล้หมดสต็อก!")
        for _, r in low_stock.iterrows():
            st.markdown(f"<div class='low-stock-card'>{r['name']} เหลือเพียง {r['qty']} ชิ้น</div>", unsafe_allow_html=True)

# --- 6. ADMIN / MANAGE ---
elif choice == "📦 จัดการคลัง":
    st.title("📦 จัดการระบบ")
    st.info("เปิดไฟล์ Google Sheets ของคุณเพื่อแก้ไขข้อมูล: [คลิกเปิดไฟล์](https://docs.google.com/spreadsheets/d/1EzHEAUtcA1Bwub0DDg3T02JiGbtnPH4IEEhhSS4oa3k/edit)")
    
    st.markdown("<div class='admin-card'>", unsafe_allow_html=True)
    st.subheader("ตรวจสอบรหัสยา (ID Check)")
    check_id = st.text_input("กรอก ID เพื่อตรวจสอบ")
    if check_id:
        match = df_stock[df_stock['id'].astype(str) == check_id]
        if not match.empty:
            st.error(f"❌ รหัส {check_id} มีอยู่แล้ว: {match.iloc[0]['name']}")
        else:
            st.success(f"✅ รหัส {check_id} ยังว่างอยู่ สามารถใช้งานได้")
    st.markdown("</div>", unsafe_allow_html=True)

elif choice == "📊 รายงาน":
    st.subheader("📊 ข้อมูลยอดขาย (ชีต2)")
    st.dataframe(df_sales, use_container_width=True)