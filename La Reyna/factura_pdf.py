import smtplib
import io
import os
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

def generar_pdf_reyna(cliente, cedula, telefono, carrito, total, metodo="Efectivo", ref=""):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    
    if os.path.exists("fondo_factura.png"):
        can.drawImage("fondo_factura.png", 0, 0, width=595, height=842)

    # --- DATOS CLIENTE ---
    can.setFont("Helvetica-Bold", 10)
    can.setFillColorRGB(1, 1, 1) 
    can.drawString(70, 560, f"CLIENTE: {cliente} | TEL: {telefono}")

    # --- DETALLE DE PRODUCTOS ---
    y_pos = 465
    can.setFont("Helvetica", 10)
    can.setFillColorRGB(1, 1, 1) 
    
    for item in carrito:
        can.drawString(85, y_pos, str(item['nombre'])[:30])
        
        # CANTIDAD: Se mantiene en su posición
        can.drawCentredString(255, y_pos, str(item['cant']))
        
        # PRECIO: Movido 1fr hacia atrás/derecha (de 335 a 355)
        try:
            p_uni = float(item['subtotal']) / int(item['cant'])
        except:
            p_uni = 0
        can.drawCentredString(355, y_pos, f"{p_uni:,.0f}")
        
        # TOTAL: Se mantiene en su posición (515)
        can.drawRightString(515, y_pos, f"{item['subtotal']:,.0f}")
        y_pos -= 22

    # --- TOTAL FACTURA ---
    can.setFont("Helvetica-Bold", 16)
    can.setFillColorRGB(0.8, 0.6, 0.2) 
    can.drawRightString(545, 255, f"CRC {total:,.2f}")

    # --- FECHA ---
    can.setFont("Helvetica-Bold", 10)
    can.setFillColorRGB(1, 1, 1)
    can.drawString(390, 105, f"{datetime.now().strftime('%d/%m/%Y')}")

    # --- INFORMACIÓN DE PAGO ---
    can.setFont("Helvetica-Bold", 12)
    can.setFillColorRGB(1, 1, 1)
    
    x_pago = 200 
    
    if metodo == "SINPE Movil":
        # Se mantiene en la ubicación que te gustó
        can.drawString(x_pago, 235, f"{ref}")
    elif metodo == "Tarjeta":
        # BAJADO 2fr adicionales (de 190 a 160) para estar bien abajo del SINPE
        can.drawString(x_pago, 160, f"{ref}")

    can.save()
    packet.seek(0)
    return packet.getvalue()

def enviar_correo_factura(destinatario, nombre_cliente, pdf_bytes, carrito):
    mi_correo = "gonzalezhg808@gmail.com"
    mi_password = "svav sfbr pqom anrk" 
    
    msg = MIMEMultipart()
    msg['From'] = f"La Reyna <{mi_correo}>"
    msg['To'] = destinatario
    msg['Subject'] = f"🧾 Factura La Reyna - {nombre_cliente}"

    cuerpo = f"Hola {nombre_cliente}, adjuntamos su comprobante de compra. ¡Gracias!"
    msg.attach(MIMEText(cuerpo, 'plain'))

    part = MIMEBase('application', 'pdf')
    part.set_payload(pdf_bytes)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment; filename="Factura_La_Reyna.pdf"')
    msg.attach(part)

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15)
        server.login(mi_correo, mi_password)
        server.send_message(msg)
        server.quit()
        print("✅ CORREO ENVIADO CON ÉXITO")
        return True
    except Exception as e:
        print(f"❌ ERROR AL ENVIAR CORREO: {e}")
        return False