from datetime import datetime
import json
import urllib.parse
import urllib.request
import streamlit as st

# ==================== CONFIGURACIÓN DE SUPABASE ====================
SUPABASE_URL = "https://nqkkawskxppmoiehaacq.supabase.co/rest/v1"
SUPABASE_KEY = "sb_publishable_AzY_OP50_vaXL30PrleYrA_ePmmH_Bv"
TABLA = "Pedidos"

def supabase_request(endpoint, method="GET", data=None, query_params=""):
  base = SUPABASE_URL.rstrip("/")
  ep = endpoint.strip("/")
  # Usamos directamente la base y le sumamos la tabla o endpoint de forma limpia
  url = f"{base}/{ep}"
  if query_params:
    url += f"?{query_params}"

  headers = {
      "apikey": SUPABASE_KEY,
      "Authorization": f"Bearer {SUPABASE_KEY}",
      "Content-Type": "application/json",
      "Accept": "application/json",
      "Prefer": "return=representation",
  }

  req_data = json.dumps(data).encode("utf-8") if data else None

  try:
    req = urllib.request.Request(
        url, data=req_data, headers=headers, method=method
    )
    with urllib.request.urlopen(req) as response:
      body = response.read().decode("utf-8")
      return json.loads(body) if body else []
  except urllib.error.HTTPError as e:
    error_body = e.read().decode("utf-8")
    st.error(f"Error en la nube ({e.code}): {error_body}")
    return []
  except Exception as e:
    st.error(f"Error: {e}")
    return []


st.set_page_config(
    page_title="PC Cristales - Pedidos", page_icon="🪟", layout="centered"
)

st.title("🪟 PC Cristales - Control de Pedidos")

# Menú lateral
menu = st.sidebar.selectbox(
    "Menú", ["Ver / Gestionar Pedidos", "Registrar Nuevo Pedido"]
)

if menu == "Registrar Nuevo Pedido":
  st.subheader("Crear un Nuevo Pedido")
  with st.form("form_pedido"):
    cliente_id = st.text_input("ID Cliente")
    recibo = st.text_input("Recibo")
    fecha = st.date_input("Fecha del Pedido", datetime.now())
    nombre = st.text_input("Nombre y Apellido del Cliente")
    concepto = st.text_input("Concepto (ej. Espejo biselado)")
    asignado = st.text_input("Encargado / Taller")
    entrega = st.date_input("Fecha Estimada de Entrega", datetime.now())

    submitted = st.form_submit_button("Guardar Pedido en la Nube")
    if submitted:
      if not cliente_id or not nombre or not concepto:
        st.warning("⚠️ ID Cliente, Nombre y Concepto son obligatorios.")
      else:
        payload = {
            "cliente_id": cliente_id,
            "recibo": recibo,
            "fecha": fecha.strftime("%Y-%m-%d"),
            "nombre_apellido": nombre,
            "concepto": concepto,
            "asignado_a": asignado,
            "estado_pedido": "Pendiente",
            "fecha_entrega": entrega.strftime("%Y-%m-%d"),
        }
        res = supabase_request(TABLA, method="POST", data=payload)
        if res is not None:
          st.success(f"¡Pedido de {nombre} registrado con éxito!")

else:
  st.subheader("Lista de Pedidos Sincronizados")

  if st.button("🔄 Sincronizar Datos"):
    st.rerun()

  data = supabase_request(TABLA, method="GET", query_params="select=*")

  if data:
    for item in data:
      with st.expander(
          f"ID: {item.get('cliente_id')} | {item.get('nombre_apellido')} — [{item.get('estado_pedido', 'Pendiente')}]"
      ):
        st.write(f"**Recibo:** {item.get('recibo')}")
        st.write(f"**Fecha:** {item.get('fecha')}")
        st.write(f"**Concepto:** {item.get('concepto')}")
        st.write(f"**Encargado:** {item.get('asignado_a')}")
        st.write(f"**Fecha Entrega:** {item.get('fecha_entrega')}")

        nuevo_estado = st.selectbox(
            "Cambiar estado",
            ["Pendiente", "Realizado", "Entregado"],
            key=f"est_{item.get('cliente_id')}",
        )

        col1, col2 = st.columns(2)
        with col1:
          if st.button(
              "Actualizar Estado", key=f"btn_up_{item.get('cliente_id')}"
          ):
            supabase_request(
                TABLA,
                method="PATCH",
                data={"estado_pedido": nuevo_estado},
                query_params=f"cliente_id=eq.{item.get('cliente_id')}",
            )
            st.success("¡Estado actualizado!")
            st.rerun()

        with col2:
          mensaje = (
              f" *PC CRISTALES - ACTUALIZACIÓN DE PEDIDO*\n\n"
              f" *ID Cliente:* #{item.get('cliente_id')} (Recibo: {item.get('recibo')})\n"
              f" *Cliente:* {item.get('nombre_apellido')}\n"
              f" *Concepto:* {item.get('concepto')}\n"
              f" *Nuevo Estado:* *{nuevo_estado}*\n"
              f" *Encargado:* {item.get('asignado_a')}"
          )
          url_wa = f"https://wa.me/?text={urllib.parse.quote(mensaje)}"
          st.markdown(
              f'<a href="{url_wa}" target="_blank" style="display:inline-block;padding:0.4em 0.8em;background-color:#25D366;color:white;text-decoration:none;border-radius:4px;font-weight:bold;font-size:14px;">📲 Enviar WhatsApp</a>',
              unsafe_allow_html=True,
          )
  else:
    st.info("No hay pedidos registrados todavía o la tabla está vacía.")
