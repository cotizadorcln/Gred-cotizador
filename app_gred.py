#!/usr/bin/env python3
"""
Grupo GRED - Cotizador simple estilo Ventti
"""

import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import os
from cotizador_gred import generar_cotizacion, load_prices

st.set_page_config(page_title="Grupo GRED Cotizador", page_icon="❄️", layout="wide")

DB = "precios_gred.db"

def get_conn():
    return sqlite3.connect(DB)

st.title("❄️ Grupo GRED · Cotizador")
st.caption("Cotizaciones rápidas · Lista de precios Hisense · Estilo Ventti")

tab1, tab2, tab3 = st.tabs(["Nueva Cotización", "Productos", "Config"])

with tab1:
    st.subheader("Crear cotización")
    cliente = st.text_input("Cliente", value="Cliente")
    moneda = st.radio("Moneda", ["USD", "MXN"], horizontal=True)
    
    products, tc, inc = load_prices()
    modelos = sorted(products.keys())
    
    st.write("**Agregar productos**")
    cols = st.columns([3, 1, 1])
    with cols[0]:
        modelo = st.selectbox("Modelo", modelos, format_func=lambda m: f"{m} · {products[m]['tipo']} · {products[m]['capacidad']}")
    with cols[1]:
        cant = st.number_input("Cantidad", min_value=1, value=1, step=1)
    with cols[2]:
        st.write("")
        st.write("")
        add = st.button("➕ Agregar")
    
    # "items" collides with SessionStateProxy.items(); use a non-method key.
    if "quote_items" not in st.session_state:
        st.session_state.quote_items = []
    
    if add and modelo:
        st.session_state.quote_items.append({"modelo": modelo, "cant": cant})
        st.success(f"Agregado {cant} x {modelo}")
    
    if st.session_state.quote_items:
        st.write("**Productos en cotización:**")
        for i, it in enumerate(st.session_state.quote_items):
            p = products[it["modelo"]]
            unit = p["usd"] if moneda == "USD" else p["mxn"]
            st.write(f"{it['cant']} × {it['modelo']} ({p['capacidad']}) — {unit:,.2f}")
        
        if st.button("🗑️ Limpiar"):
            st.session_state.quote_items = []
            st.rerun()
        
        if st.button("📄 Generar PDF", type="primary"):
            path, total, mon = generar_cotizacion(st.session_state.quote_items, cliente=cliente, moneda=moneda)
            st.success(f"Cotización generada · Total: {mon} {total:,.2f}")
            with open(path, "rb") as f:
                st.download_button("⬇️ Descargar PDF", f, file_name=os.path.basename(path), mime="application/pdf")

with tab2:
    st.subheader("Lista de precios")
    st.write(f"TC: **{tc}** · Incremento: **{int(inc*100)}%**")
    data = []
    for m, p in sorted(products.items()):
        data.append({
            "Modelo": m,
            "Tipo": p["tipo"],
            "Capacidad": p["capacidad"],
            "USD": round(p["usd"], 2),
            "MXN (+35%)": round(p["mxn"], 2)
        })
    st.dataframe(data, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Configuración")
    st.info("Base de datos local: precios_gred.db")
    st.write("Para actualizar precios, sube una nueva lista de Drive y reinicia la DB.")
    if st.button("Recargar precios desde Excel"):
        st.warning("Función pendiente – usa el script de importación.")
