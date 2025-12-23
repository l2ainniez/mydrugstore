import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import time

# --- 1. SETTING & UI STYLE ---
st.set_page_config(page_title="Cloud Drugstore POS", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; background-color: #1A202C !important; color: #E2E8F0 !important; }
    
    .cart-row-container {
        background-color: #F7FAFC !important;
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
    .admin-header { font-size: 1.4rem; font-weight: 700; color: #63B3ED; margin-bottom: 15px; border-left: 5px solid #63B3ED; padding-left: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 2. CONNECT TO GOOGLE SHEETS ---
# ใส่ลิงก์จากไฟล์ "คลังยาออนไลน์" เรียบร้อยครับ 
sheet_url = "https://docs.google.com/spreadsheets/d/1EzHEAUtcA1Bwub0DDg3T02JiGbtnPH4IEEhhSS4oa3k/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

def get_stock_data():
    return conn.read(spreadsheet=sheet_url, worksheet="stock", ttl="0")

def get_sales_data():
    # ปรับชื่อชีตตามที่คุณตั้งไว้คือ "ชีต2" 
    return conn.read(spreadsheet=sheet_url, worksheet="ชีต2", ttl="0")

# --- 3. MAIN NAVIGATION ---
with st.sidebar:
    st.markdown("<div style='text-align: center; padding: 25px 0px 40px 0px;'><h1 style='color: #63B3ED; margin: 0; font-size: 2.2rem; letter-spacing: 3px; font-weight: 900;'>💊 PHARMA</h1></div>", unsafe_allow_html=True)
    choice = st.radio("เมนูหลัก", ["🛒 ขายสินค้า", "⚠️ ยาใกล้หมด", "📋 เช็คสต็อก", "📦 จัดการคลัง", "📊 รายงาน"], label_visibility="collapsed")

df_stock = get_stock_data()

# --- 4. SALES LOGIC ---
if choice == "🛒 ขายสินค้า":
    if 'cart' not in st.session_state: st.session_state.cart = {}
    col_left, col_right = st.columns([1, 1.2])
    
    with col_left:
        st.subheader("🔍 ค้นหาและเลือกสินค้า")
        search_input = st.text_input("พิมพ์ชื่อยาหรือยิงบาร์โค้ด", placeholder="Barcode / Search...")
        
        available_stock = df_stock[df_stock['qty'] > 0]
        item_list = ["-- เลือกรายการยา --"] + [f"{r['name']} | คงเหลือ: {r['qty']}" for _, r in available_stock.iterrows()]
        
        current_idx = 0
        if search_input:
            for i, item in enumerate(item_list):
                if search_input.lower() in item.lower():
                    current_idx = i; break
        
        selected = st.selectbox("เลือกรายการ", item_list, index=current_idx, label_visibility="collapsed")
        
        if selected != "-- เลือกรายการยา --":
            item_name = selected.split(" | ")[0]
            item_info = df_stock[df_stock['name'] == item_name].iloc[0]
            st.info(f"ราคา: ฿{float(item_info['price']):.2f} | ID: {item_info['id']}")
            if st.button("➕ เพิ่มลงตะกร้า", use_container_width=True, type="primary"):
                i_id = str(item_info['id'])
                if i_id in st.session_state.cart:
                    if st.session_state.cart[i_id]['qty'] < item_info['qty']:
                        st.session_state.cart[i_id]['qty'] += 1
                else:
                    st.session_state.cart[i_id] = {'name': item_info['name'], 'price': item_info['price'], 'qty': 1, 'max': item_info['qty']}
                st.rerun()

    with col_right:
        st.subheader("🛒 ตะกร้าสินค้า")
        if not st.session_state.cart: st.info("ตะกร้าว่างเปล่า")
        else:
            total = 0
            for tid, info in list(st.session_state.cart.items()):
                total += (int(info['qty']) * float(info['price']))
                st.markdown(f'<div class="cart-row-container">', unsafe_allow_html=True)
                c_n, c_q, c_d = st.columns([2, 1.5, 0.5])
                c_n.markdown(f"<div class='cart-item-name'>{info['name']}</div><div class='cart-price-sub'>฿{float(info['price']):,.2f}</div>", unsafe_allow_html=True)
                with c_q:
                    q1, q2, q3 = st.columns([1, 1, 1])
                    if q1.button("−", key=f"m_{tid}"):
                        if st.session_state.cart[tid]['qty'] > 1: st.session_state.cart[tid]['qty'] -= 1
                        else: del st.session_state.cart[tid]
                        st.rerun()
                    q2.markdown(f"<div class='cart-qty-num'>{info['qty']}</div>", unsafe_allow_html=True)
                    if q3.button("＋", key=f"p_{tid}"):
                        if info['qty'] < info['max']: st.session_state.cart[tid]['qty'] += 1
                        st.rerun()
                if c_d.button("🗑️", key=f"d_{tid}"): del st.session_state.cart[tid]; st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown(f"<div style='text-align: right;'><h2 style='color: #63B3ED;'>ยอดรวม ฿{total:,.2f}</h2></div>", unsafe_allow_html=True)
            if st.button("💰 ยืนยันชำระเงิน", use_container_width=True, type="primary"):
                new_sales = []
                for tid, info in st.session_state.cart.items():
                    df_stock.loc[df_stock['id'].astype(str) == tid, 'qty'] -= info['qty']
                    new_sales.append([datetime.now().strftime("%Y-%m-%d %H:%M"), tid, info['name'], info['qty'], info['qty']*info['price']])
                
                conn.update(spreadsheet=sheet_url, worksheet="stock", data=df_stock)
                df_sales = get_sales_data()
                df_sales = pd.concat([df_sales, pd.DataFrame(new_sales, columns=df_sales.columns)], ignore_index=True)
                conn.update(spreadsheet=sheet_url, worksheet="ชีต2", data=df_sales)
                
                st.session_state.cart = {}
                st.success("ชำระเงินสำเร็จ!"); time.sleep(1); st.rerun()

# --- 5. STOCK MANAGEMENT ---
elif choice == "📦 จัดการคลัง":
    st.title("📦 จัดการคลังสินค้า (Google Sheets)")
    t1, t2, t3 = st.tabs(["✨ ลงทะเบียนใหม่", "📈 เติมสต็อก", "🗑️ ลบรายการ"])
    
    with t1:
        st.markdown("<div class='admin-card'>", unsafe_allow_html=True)
        n_id = st.text_input("รหัสยา (ID / Barcode)")
        id_exists = False
        if n_id:
            match = df_stock[df_stock['id'].astype(str) == n_id]
            if not match.empty:
                st.error(f"❌ รหัส '{n_id}' นี้ซ้ำกับรายการ: **{match.iloc[0]['name']}**")
                id_exists = True
        
        n_name = st.text_input("ชื่อยา")
        n_price = st.number_input("ราคา", min_value=0.0)
        n_qty = st.number_input("จำนวนเริ่มต้น", min_value=0)
        
        if st.button("💾 บันทึก", disabled=id_exists, type="primary"):
            new_row = pd.DataFrame([[n_id, n_name, n_qty, n_price]], columns=df_stock.columns)
            df_updated = pd.concat([df_stock, new_row], ignore_index=True)
            conn.update(spreadsheet=sheet_url, worksheet="stock", data=df_updated)
            st.success("บันทึกแล้ว"); time.sleep(1); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    with t2:
        st.markdown("<div class='admin-card'>", unsafe_allow_html=True)
        target = st.selectbox("เลือกยา", df_stock['name'].tolist())
        add_q = st.number_input("จำนวนที่เติม", min_value=1)
        if st.button("📈 ยืนยันเติมสต็อก"):
            df_stock.loc[df_stock['name'] == target, 'qty'] += add_q
            conn.update(spreadsheet=sheet_url, worksheet="stock", data=df_stock)
            st.success("อัปเดตแล้ว"); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with t3:
        st.markdown("<div class='admin-card'>", unsafe_allow_html=True)
        del_target = st.selectbox("เลือกรายการที่จะลบ", df_stock['name'].tolist())
        conf = st.checkbox("ยืนยันการลบ")
        if st.button("🗑️ ยืนยันการลบทิ้ง", disabled=not conf):
            df_stock = df_stock[df_stock['name'] != del_target]
            conn.update(spreadsheet=sheet_url, worksheet="stock", data=df_stock)
            st.success("ลบรายการแล้ว"); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif choice == "⚠️ ยาใกล้หมด":
    low_stock = df_stock[df_stock['qty'].astype(int) <= 2]
    if low_stock.empty:
        st.info("ไม่มียาใกล้หมดในขณะนี้")
    else:
        for _, r in low_stock.iterrows():
            st.markdown(f"<div class='low-stock-card'><b>{r['name']}</b> (ID: {r['id']}) <br>เหลือเพียง: {r['qty']}</div>", unsafe_allow_html=True)

elif choice == "📊 รายงาน":
    st.subheader("📊 ยอดขายจาก Google Sheets")
    df_sales = get_sales_data()
    if not df_sales.empty:
        st.metric("ยอดขายรวม", f"฿{df_sales['total'].astype(float).sum():,.2f}")
        st.dataframe(df_sales, use_container_width=True, hide_index=True)
    else:
        st.info("ยังไม่มีข้อมูลการขาย")

elif choice == "📋 เช็คสต็อก":
    st.subheader("📋 รายการสินค้าคงคลังทั้งหมด")
    st.dataframe(df_stock, use_container_width=True, hide_index=True)