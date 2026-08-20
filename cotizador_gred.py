#!/usr/bin/env python3
"""
Cotizador Grupo GRED - Hisense LCAC
Base de datos local SQLite (precios_gred.db) + lista de Drive
"""

import sqlite3
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from datetime import datetime, timedelta
import os

# Config
DB_PATH = "precios_gred.db"
LOGO_PATH = "logo_gred.png"
OUTPUT_DIR = "."

DARK_BLUE = colors.HexColor('#1a3a6b')
LIGHT_GRAY = colors.HexColor('#f5f5f5')
MED_GRAY = colors.HexColor('#e8e8e8')

def load_prices():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    tc = c.execute("SELECT value FROM config WHERE key='tc'").fetchone()[0]
    inc = c.execute("SELECT value FROM config WHERE key='incremento'").fetchone()[0]
    products = {}
    for row in c.execute("SELECT modelo, tipo, capacidad, descripcion, usd, mxn FROM productos"):
        modelo, tipo, cap, desc, usd, mxn = row
        products[modelo] = {
            'tipo': tipo or '',
            'capacidad': cap or '',
            'descripcion': desc or '',
            'usd': float(usd),
            'mxn': float(mxn)
        }
    conn.close()
    return products, tc, inc

def money(v, currency='MXN'):
    if currency == 'USD':
        return f"US$ {v:,.2f}"
    return f"$ {v:,.2f}"

def generar_cotizacion(items, cliente="Cliente", moneda='MXN', iva=0.08, output_name=None):
    """
    items: list of dicts {'modelo': 'AUC-60TR5R', 'cant': 7}
    """
    products, tc, inc = load_prices()
    
    lineas = []
    subtotal = 0.0
    for it in items:
        modelo = it['modelo']
        cant = it['cant']
        if modelo not in products:
            raise ValueError(f"Modelo no encontrado: {modelo}")
        p = products[modelo]
        unit = p['usd'] if moneda == 'USD' else p['mxn']
        importe = round(unit * cant, 2)
        subtotal += importe
        lineas.append({
            'cant': cant,
            'modelo': modelo,
            'tipo': p['tipo'],
            'cap': p['capacidad'],
            'desc': p['descripcion'][:80] + '...' if len(p['descripcion']) > 80 else p['descripcion'],
            'unit': unit,
            'importe': importe
        })
    
    iva_monto = round(subtotal * iva, 2)
    total = round(subtotal + iva_monto, 2)
    
    if not output_name:
        ts = datetime.now().strftime('%Y%m%d_%H%M')
        output_name = f"Cotizacion_GRED_{ts}.pdf"
    out_path = os.path.join(OUTPUT_DIR, output_name)
    
    # Build PDF
    doc = SimpleDocTemplate(out_path, pagesize=letter,
                            leftMargin=0.5*inch, rightMargin=0.5*inch,
                            topMargin=0.4*inch, bottomMargin=0.4*inch)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleOC', parent=styles['Normal'], fontName='Helvetica-Bold',
                                 fontSize=14, textColor=DARK_BLUE, alignment=TA_CENTER, spaceAfter=4)
    header_cell = ParagraphStyle('HeaderCell', parent=styles['Normal'], fontName='Helvetica-Bold',
                                 fontSize=8, textColor=colors.white, alignment=TA_CENTER, leading=10)
    normal_small = ParagraphStyle('NormalSmall', parent=styles['Normal'], fontName='Helvetica',
                                  fontSize=8, leading=10, alignment=TA_LEFT)
    normal_tiny = ParagraphStyle('NormalTiny', parent=styles['Normal'], fontName='Helvetica',
                                 fontSize=7.5, leading=9, alignment=TA_LEFT)
    center_small = ParagraphStyle('CenterSmall', parent=styles['Normal'], fontName='Helvetica',
                                  fontSize=8, alignment=TA_CENTER)
    right_small = ParagraphStyle('RightSmall', parent=styles['Normal'], fontName='Helvetica',
                                 fontSize=8, alignment=TA_RIGHT)
    right_bold = ParagraphStyle('RightBold', parent=styles['Normal'], fontName='Helvetica-Bold',
                                fontSize=9, alignment=TA_RIGHT)
    
    logo = Image(LOGO_PATH, width=2.2*inch, height=1.04*inch)
    logo.hAlign = 'CENTER'
    
    fecha = datetime.now().strftime('%d de %B de %Y').replace('August', 'agosto').replace('September', 'septiembre')
    valida = (datetime.now() + timedelta(days=15)).strftime('%d de %B de %Y').replace('August', 'agosto').replace('September', 'septiembre')
    
    info_data = [[
        Paragraph(f"<b>No.:</b> COT-{datetime.now().strftime('%Y%m%d-%H%M')}", normal_small),
        Paragraph(f"<b>Fecha:</b> {fecha}", normal_small),
        Paragraph(f"<b>Válida hasta:</b> {valida}", normal_small),
    ]]
    info_table = Table(info_data, colWidths=[2.4*inch, 2.5*inch, 2.6*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), MED_GRAY),
        ('BOX', (0, 0), (-1, -1), 0.5, DARK_BLUE),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    # Proveedor / Comprador simplified
    prov_comp = [[
        Paragraph("<b>PROVEEDOR</b>", header_cell),
        Paragraph("<b>COMPRADOR</b>", header_cell),
    ],[
        Paragraph("<b>Grupo GRED</b><br/>José Ángel Cisneros Santiago<br/>RFC: CISA7808119H9<br/>Tijuana, Baja California<br/>Tel. 667 185 0455", normal_tiny),
        Paragraph(f"<b>{cliente}</b><br/><br/><br/><br/>", normal_tiny),
    ]]
    prov_table = Table(prov_comp, colWidths=[3.75*inch, 3.75*inch])
    prov_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), DARK_BLUE),
        ('BOX', (0, 0), (-1, -1), 0.7, DARK_BLUE),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, DARK_BLUE),
        ('TOPPADDING', (0, 0), (-1, 0), 4),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
        ('TOPPADDING', (0, 1), (-1, 1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    # Table header
    rows = [[
        Paragraph("<b>CANT.</b>", header_cell),
        Paragraph("<b>DESCRIPCIÓN</b>", header_cell),
        Paragraph("<b>P. UNITARIO</b>", header_cell),
        Paragraph("<b>IMPORTE</b>", header_cell),
    ]]
    
    for i, l in enumerate(lineas):
        desc = f"{l['modelo']} · {l['tipo']} · {l['cap']}<br/>{l['desc']}"
        rows.append([
            Paragraph(str(l['cant']), center_small),
            Paragraph(desc, normal_tiny),
            Paragraph(money(l['unit'], moneda), right_small),
            Paragraph(money(l['importe'], moneda), right_small),
        ])
    
    # Totals
    cur_label = 'USD' if moneda == 'USD' else 'MXN'
    totals = [
        [Paragraph("", normal_small), Paragraph("", normal_small),
         Paragraph(f"<b>Subtotal ({cur_label}):</b>", right_small),
         Paragraph(money(subtotal, moneda), right_bold)],
        [Paragraph("", normal_small), Paragraph("", normal_small),
         Paragraph(f"<b>IVA {int(iva*100)}%:</b>", right_small),
         Paragraph(money(iva_monto, moneda), right_bold)],
        [Paragraph("", normal_small), Paragraph("", normal_small),
         Paragraph(f"<b>TOTAL ({cur_label} + IVA):</b>", right_bold),
         Paragraph(money(total, moneda), right_bold)],
    ]
    
    n_items = len(lineas)
    prod_table = Table(rows + totals, colWidths=[0.6*inch, 4.3*inch, 1.3*inch, 1.3*inch])
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), DARK_BLUE),
        ('BOX', (0, 0), (-1, n_items), 0.7, DARK_BLUE),
        ('INNERGRID', (0, 0), (-1, n_items), 0.4, DARK_BLUE),
        ('LINEABOVE', (2, n_items+1), (-1, n_items+1), 0.5, DARK_BLUE),
        ('LINEABOVE', (2, n_items+3), (-1, n_items+3), 1, DARK_BLUE),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
    ]
    for i in range(1, n_items+1):
        bg = LIGHT_GRAY if i % 2 == 1 else colors.white
        style_cmds.append(('BACKGROUND', (0, i), (-1, i), bg))
    prod_table.setStyle(TableStyle(style_cmds))
    
    nota = Paragraph(
        f"<b>Notas:</b> Precios basados en lista Hisense Grupo GRED. "
        f"TC: {tc:.3f} MXN/USD · Incremento: {int(inc*100)}%. "
        f"IVA {int(iva*100)}%. Válida 15 días.",
        normal_tiny
    )
    
    sig_data = [[
        Paragraph("_______________________________<br/><b>José Ángel Cisneros</b><br/>Grupo GRED / Vendedor", center_small),
        Paragraph("_______________________________<br/><b>Cliente</b><br/>Aceptación", center_small),
    ]]
    sig_table = Table(sig_data, colWidths=[3.75*inch, 3.75*inch])
    sig_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 20),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    footer = Paragraph(
        f"Grupo GRED · Documento comercial · Precios {cur_label} (TC {tc:.3f})",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=7, textColor=colors.gray, alignment=TA_CENTER)
    )
    
    story = [
        logo,
        Spacer(1, 2),
        Paragraph("Aire Acondicionado y Climas · Tel. 667 185 0455 · ventas@grupogred.com",
                  ParagraphStyle('Sub', parent=styles['Normal'], fontSize=7, alignment=TA_CENTER, textColor=colors.gray)),
        Spacer(1, 6),
        Paragraph("COTIZACIÓN", title_style),
        Spacer(1, 4),
        info_table,
        Spacer(1, 8),
        prov_table,
        Spacer(1, 8),
        prod_table,
        Spacer(1, 8),
        nota,
        Spacer(1, 16),
        sig_table,
        Spacer(1, 12),
        footer,
    ]
    
    doc.build(story)
    return out_path, total, cur_label

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Cotizador Grupo GRED - Hisense")
    parser.add_argument("items", nargs="*", help="Formato: MODELO:CANT  ej. AUC-60TR5R:7 AUD-36UX4SEH5:5")
    parser.add_argument("--cliente", default="Cliente", help="Nombre del cliente")
    parser.add_argument("--moneda", choices=["USD", "MXN"], default="USD", help="Moneda (default USD)")
    parser.add_argument("--listar", action="store_true", help="Listar productos disponibles")
    args = parser.parse_args()

    if args.listar or not args.items:
        products, tc, inc = load_prices()
        print(f"TC: {tc} | Incremento: {int(inc*100)}%\n")
        print(f"{'MODELO':15} {'TIPO':12} {'CAPACIDAD':15} {'USD':>10}")
        print("-"*55)
        for m, p in sorted(products.items()):
            print(f"{m:15} {p['tipo'][:12]:12} {p['capacidad'][:15]:15} {p['usd']:10.2f}")
        if not args.items:
            print("\nUso: python3 cotizador_gred.py MODELO:CANT [MODELO:CANT ...] [--cliente NOMBRE] [--moneda USD|MXN]")
            print("Ej:  python3 cotizador_gred.py AUC-60TR5R:7 AUC-36TR5R:7 AUD-36UX4SEH5:5 --cliente 'Hector Reyes'")
    else:
        items = []
        for it in args.items:
            if ":" not in it:
                print(f"Error: formato inválido '{it}'. Usa MODELO:CANT")
                exit(1)
            modelo, cant = it.split(":", 1)
            items.append({"modelo": modelo.strip(), "cant": int(cant)})
        path, total, mon = generar_cotizacion(items, cliente=args.cliente, moneda=args.moneda)
        print(f"Generado: {path}")
        print(f"Total: {mon} {total:,.2f}")
