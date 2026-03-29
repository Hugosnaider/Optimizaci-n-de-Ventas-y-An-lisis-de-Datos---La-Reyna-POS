import streamlit as st
import pandas as pd
from database import DBManager
from factura_pdf import generar_pdf_reyna, enviar_correo_factura
from datetime import datetime
import plotly.express as px

# 1. CONFIGURACIÓN Y ESTILOS
st.set_page_config(page_title="La Reyna POS", layout="wide", page_icon="👑")

st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background: linear-gradient(135deg, #7A1E8D 0%, #4F105F 100%) !important; }
    [data-testid="stSidebar"] { background-color: #350a40 !important; border-right: 3px solid #FFB800; }
    .header-reyna { text-align: center; color: #FFB800; font-size: 55px; font-weight: 900; text-shadow: 3px 3px 12px rgba(0,0,0,0.6); }
    .stButton>button { background-color: #FFB800 !important; color: black !important; font-weight: bold; border-radius: 15px; height: 55px; width: 100%; border: none; }
    .pantalla-monto { background-color: #FFB800; color: black !important; padding: 40px; border-radius: 30px; text-align: center; border: 8px solid white; margin-bottom: 25px; }
    .monto-gigante { font-size: 110px !important; font-weight: 900 !important; color: black !important; margin: 0; }
    p, label, .stMarkdown, h1, h2, h3 { color: white !important; }
    .widget-reyna { background: rgba(255,184,0,0.15); border: 1px solid #FFB800; padding: 20px; border-radius: 20px; text-align: center; }
</style>
""", unsafe_allow_html=True)

db = DBManager()

# --- ESTADOS DE SESIÓN ---
for key in ['autenticado', 'carrito', 'last_carrito', 'cobrando', 'venta_finalizada', 'temp_venta', 'user_nom', 'user_rol']:
    if key not in st.session_state:
        if key in ['carrito', 'last_carrito']:
            st.session_state[key] = []
        elif key in ['user_nom', 'user_rol']:
            st.session_state[key] = ""
        elif key == 'temp_venta':
            st.session_state[key] = {}
        else:
            st.session_state[key] = False

# --- LOGIN ---
if not st.session_state.autenticado:
    st.markdown('<div class="header-reyna">👑 LA REYNA 👑</div>', unsafe_allow_html=True)
    with st.columns([1, 1.2, 1])[1]:
        u_in = st.text_input("Usuario")
        p_in = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR"):
            res = db.ejecutar("SELECT * FROM usuarios WHERE nombre_usuario = %s AND clave = %s", (u_in, p_in), fetch=True)
            if res:
                st.session_state.autenticado = True
                st.session_state.user_nom = res[0]['nombre_usuario']
                st.session_state.user_rol = res[0]['rol'].lower()
                st.rerun()
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='color: #FFB800; text-align: center;'>👑 LA REYNA</h1>", unsafe_allow_html=True)
    opciones = ["🛒 VENTAS", "📦 INVENTARIO", "📊 MÉTRICAS", "💰 ARQUEO", "👥 USUARIOS"]
    if st.session_state.user_rol != "admin":
        opciones = ["🛒 VENTAS", "💰 ARQUEO"]
    menu = st.radio("MENÚ", opciones)
    
    if st.button("🚪 CERRAR SESIÓN"):
        st.session_state.autenticado = False
        st.rerun()

# --- CONTENEDOR PRINCIPAL ---
with st.container():
    
    # 🛒 SECCIÓN DE VENTAS
    if menu == "🛒 VENTAS":
        res_hoy = db.ejecutar("SELECT COUNT(*) as cuenta, SUM(total) as suma FROM ventas WHERE fecha::date = CURRENT_DATE", fetch=True)
        v_hoy = res_hoy[0]['cuenta'] if res_hoy and res_hoy[0]['cuenta'] else 0
        m_hoy = res_hoy[0]['suma'] if res_hoy and res_hoy[0]['suma'] else 0

        w1, w2, w3 = st.columns(3)
        w1.markdown(f'<div class="widget-reyna">Ventas Hoy: <b>{v_hoy}</b></div>', unsafe_allow_html=True)
        w2.markdown(f'<div class="widget-reyna">Monto: <b>₡{m_hoy:,.0f}</b></div>', unsafe_allow_html=True)
        w3.markdown(f'<div class="widget-reyna">Estado: <b>ABIERTA</b></div>', unsafe_allow_html=True)

        if st.session_state.venta_finalizada:
            v = st.session_state.temp_venta
            st.markdown('<div class="header-reyna">Venta Exitosa ✅</div>', unsafe_allow_html=True)
            pdf_data = generar_pdf_reyna(v['cliente'], "0", v.get('telefono', '8888-8888'), st.session_state.last_carrito, v['total'], metodo=v.get('metodo'))
            
            c1, c2, c3 = st.columns(3)
            c1.download_button("📥 PDF", data=pdf_data, file_name=f"Factura_{v['cliente']}.pdf")
            with c2:
                correo = st.text_input("Email")
                if st.button("📧 ENVIAR"):
                    if correo and enviar_correo_factura(correo, v['cliente'], pdf_data, st.session_state.last_carrito):
                        st.toast("🚀 ¡Enviado!")
            c3.link_button("📱 WHATSAPP", f"https://wa.me/506{v.get('telefono', '88888888')}")
            
            if st.button("🔄 NUEVA VENTA"):
                st.session_state.venta_finalizada = False
                st.session_state.carrito = []
                st.rerun()

        elif st.session_state.cobrando:
            v = st.session_state.temp_venta
            st.markdown(f'<div class="pantalla-monto"><h2>TOTAL A COBRAR</h2><p class="monto-gigante">₡{v["total"]:,.0f}</p></div>', unsafe_allow_html=True)
            
            pago = st.selectbox("Método de Pago", ["Efectivo", "Tarjeta", "SINPE Movil", "Mixto"], key="sel_metodo_pago")
            metodo_final = pago

            if pago == "Mixto":
                st.markdown('<div style="background: rgba(255,184,0,0.1); padding: 20px; border-radius: 15px; border: 1px solid #FFB800;">', unsafe_allow_html=True)
                col_e, col_d = st.columns(2)
                monto_efe = col_e.number_input("Monto en EFECTIVO ₡", min_value=0.0, max_value=float(v["total"]), value=0.0, step=500.0, key="input_mixto_efe")
                monto_dig = float(v["total"]) - monto_efe
                col_d.markdown(f"<br><h3>Digital: ₡{monto_dig:,.0f}</h3>", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                metodo_final = f"Mixto (Efe: ₡{monto_efe:,.0f} / Dig: ₡{monto_dig:,.0f})"

            if st.button("✅ FINALIZAR Y REGISTRAR"):
                for i in st.session_state.carrito:
                    db.ejecutar("INSERT INTO ventas (producto_id, cantidad, total, metodo_pago, cliente_info, fecha) VALUES (%s,%s,%s,%s,%s, NOW())", 
                                (i['id'], i['cant'], i['subtotal'], metodo_final, v['cliente']))
                    db.ejecutar("UPDATE productos SET stock = stock - %s WHERE id = %s", (i['cant'], i['id']))
                st.session_state.last_carrito = st.session_state.carrito.copy()
                st.session_state.temp_venta['metodo'] = metodo_final
                st.session_state.venta_finalizada, st.session_state.cobrando = True, False
                st.rerun()
            
            if st.button("⬅️ VOLVER AL CARRITO"):
                st.session_state.cobrando = False
                st.rerun()

        else:
            st.markdown('<div class="header-reyna">🛒 CAJA</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            c_nom = c1.text_input("Cliente", "Consumidor Final")
            c_tel = c2.text_input("Tel", "8888-8888")

            res_p = db.ejecutar('SELECT id, nombre, precio, stock FROM productos WHERE stock > 0 ORDER BY nombre ASC', fetch=True)
            if res_p:
                df_p = pd.DataFrame(res_p)
                p_sel = st.selectbox("Seleccione Producto", df_p['nombre'].tolist())
                det = df_p[df_p['nombre'] == p_sel].iloc[0]
                
                # MEJORA 1: Validación de Stock en el input
                cant = st.number_input(f"Cantidad (Disponible: {int(det['stock'])})", 1, int(det['stock']), 1)
                
                if st.button("➕ AÑADIR AL CARRITO"):
                    st.session_state.carrito.append({
                        "id": int(det['id']), "nombre": det['nombre'], "precio": float(det['precio']), 
                        "cant": int(cant), "subtotal": float(det['precio'] * cant)
                    })
                    st.toast(f"✅ {det['nombre']} añadido")
                    st.rerun()

            if st.session_state.carrito:
                st.markdown("---")
                total = sum(i['subtotal'] for i in st.session_state.carrito)
                for i in st.session_state.carrito:
                    st.write(f"• **{i['nombre']}** (x{i['cant']}) - ₡{i['subtotal']:,.0f}")
                st.markdown(f"<h2 style='text-align: right; color: #FFB800;'>TOTAL: ₡{total:,.0f}</h2>", unsafe_allow_html=True)
                
                b1, b2 = st.columns(2)
                if b1.button("💰 PROCEDER AL PAGO"):
                    st.session_state.temp_venta = {"cliente": c_nom, "telefono": c_tel, "total": total}
                    st.session_state.cobrando = True
                    st.rerun()
                if b2.button("🗑️ VACIAR CARRITO"):
                    st.session_state.carrito = []
                    st.rerun()

    # 📦 SECCIÓN DE INVENTARIO
    elif menu == "📦 INVENTARIO":
        st.markdown('<div class="header-reyna">📦 ALMACÉN CENTRAL</div>', unsafe_allow_html=True)
        res = db.ejecutar("SELECT id, nombre, costo, precio, stock FROM productos ORDER BY nombre ASC", fetch=True)
        if res:
            df_inv = pd.DataFrame(res)
            
            # MEJORA 2: Alertas Visuales de Stock Bajo
            def resaltar_bajo_stock(row):
                return ['background-color: #721c24; color: white' if row.stock < 5 else '' for _ in row]
            
            st.dataframe(df_inv.style.apply(resaltar_bajo_stock, axis=1), use_container_width=True)
            
            if any(df_inv['stock'] < 5):
                st.warning("⚠️ Atención: Hay productos con existencias bajas (menos de 5 unidades).")

            with st.expander("📥 AGREGAR STOCK"):
                p_sumar = st.selectbox("Producto", df_inv['nombre'].tolist())
                n_cant = st.number_input("Cantidad", min_value=1)
                if st.button("➕ ACTUALIZAR"):
                    db.ejecutar("UPDATE productos SET stock = stock + %s WHERE nombre = %s", (n_cant, p_sumar))
                    st.rerun()
        
        with st.form("nuevo_p"):
            st.write("### ✨ Producto Nuevo")
            n_n = st.text_input("Nombre")
            c_n = st.number_input("Costo")
            p_n = st.number_input("Precio")
            s_n = st.number_input("Stock Inicial", min_value=0)
            if st.form_submit_button("✅ REGISTRAR"):
                db.ejecutar("INSERT INTO productos (nombre, costo, precio, stock) VALUES (%s,%s,%s,%s)", (n_n, c_n, p_n, s_n))
                st.rerun()

    # 📊 SECCIÓN DE MÉTRICAS
    elif menu == "📊 MÉTRICAS":
        st.markdown('<div class="header-reyna">📊 RENDIMIENTO</div>', unsafe_allow_html=True)
        query = """SELECT p.nombre, SUM(v.cantidad) as uds, SUM(v.total) as total 
                   FROM ventas v JOIN productos p ON v.producto_id = p.id GROUP BY p.nombre"""
        res = db.ejecutar(query, fetch=True)
        
        if res:
            df_metricas = pd.DataFrame(res)
            st.plotly_chart(px.bar(df_metricas, x='nombre', y='total', color='nombre', title="Ingresos Totales por Producto"))
            
            # MEJORA 3: Análisis de Pareto (80/20)
            st.markdown("---")
            st.subheader("🎯 Análisis de Pareto (Productos Estrella)")
            df_metricas = df_metricas.sort_values(by='total', ascending=False)
            df_metricas['acumulado'] = df_metricas['total'].cumsum()
            df_metricas['pct_acumulado'] = (df_metricas['acumulado'] / df_metricas['total'].sum()) * 100
            
            fig_pareto = px.line(df_metricas, x='nombre', y='pct_acumulado', title="Curva de Concentración de Ingresos")
            fig_pareto.add_bar(x=df_metricas['nombre'], y=df_metricas['total'], name="Ventas")
            st.plotly_chart(fig_pareto, use_container_width=True)
            st.info("💡 Los productos que están por debajo del 80% en la línea son tus motores de ingreso principales.")

    # 💰 ARQUEO Y USUARIOS (Se mantienen igual para no alargar el código)
    elif menu == "💰 ARQUEO":
        st.title("Arqueo Contable 💰")
        fondo_inicial = st.number_input("Fondo Inicial", value=20000.0)
        efectivo_fisico = st.number_input("Efectivo Físico", value=0.0)
        res_v = db.ejecutar("SELECT SUM(total) as total_dia FROM ventas WHERE fecha::date = current_date", fetch=True)
        ventas_sistema = float(res_v[0]['total_dia']) if res_v and res_v[0]['total_dia'] else 0.0
        dinero_esperado = fondo_inicial + ventas_sistema
        st.metric("Ventas Sistema", f"₡{ventas_sistema:,.0f}")
        st.metric("Diferencia", f"₡{efectivo_fisico - dinero_esperado:,.0f}")

    elif menu == "👥 USUARIOS":
        st.markdown('<div class="header-reyna">👥 USUARIOS</div>', unsafe_allow_html=True)
        with st.form("nuevo_u"):
            nu_nom = st.text_input("Usuario")
            nu_cla = st.text_input("Contraseña", type="password")
            nu_rol = st.selectbox("Rol", ["Admin", "Vendedor"])
            if st.form_submit_button("💾 GUARDAR"):
                db.ejecutar("INSERT INTO usuarios (nombre_usuario, clave, rol) VALUES (%s,%s,%s)", (nu_nom, nu_cla, nu_rol))
                st.rerun()