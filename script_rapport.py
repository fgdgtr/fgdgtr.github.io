#!/usr/bin/env python3
"""
AUEM Rack Weekly Report - COMPLETE VERSION
With charts, colors, and professional design
"""

import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email.encoders import encode_base64
import requests
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, String, Rect
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart

# ============================================================
# 🔧 CONFIGURATION
# ============================================================

FIREBASE_URL = 'https://auem-rac-default-rtdb.europe-west1.firebasedatabase.app/retour.json'
# Email à utiliser pour envoyer
SMTP_USER = 'k61587549@gmail.com' 
SMTP_PASSWORD = 'gnpe bpxy ljpx slib'  

# Email qui reçoit le rapport 
RAPPORT_EMAIL = 'axefoxe8592@gmail.com' 
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

# ============================================================

def fetch_firebase_data():
    try:
        response = requests.get(FIREBASE_URL)
        return response.json() if response.json() else {}
    except Exception as e:
        print(f"❌ Erreur Firebase: {e}")
        return {}

def parse_palettes(data):
    palettes = []
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                palettes.append({
                    'client': value.get('client', 'N/A'),
                    'date_entree': value.get('date_entree', 'N/A'),
                    'emplacement': value.get('emplacement', 'N/A'),
                })
    return palettes

def calculate_stats(palettes):
    today = datetime.now()
    stats = {
        'total': len(palettes),
        'par_zone': {'vert': 0, 'bleu': 0, 'jaune': 0, 'rouge': 0},
        'temps_moyen': 0,
        'critiques': [],
        'top_clients': {}
    }
    
    jours_total = 0
    
    for palette in palettes:
        client = palette.get('client', 'Unknown')
        stats['top_clients'][client] = stats['top_clients'].get(client, 0) + 1
        
        try:
            date_str = palette.get('date_entree', '')
            if date_str and len(date_str) >= 10:
                date_entree = datetime.strptime(date_str[:10], '%Y-%m-%d')
                jours = (today - date_entree).days
                jours_total += jours
                
                if jours <= 15:
                    stats['par_zone']['vert'] += 1
                elif jours <= 21:
                    stats['par_zone']['bleu'] += 1
                elif jours <= 28:
                    stats['par_zone']['jaune'] += 1
                else:
                    stats['par_zone']['rouge'] += 1
                    stats['critiques'].append({
                        'client': client,
                        'emplacement': palette.get('emplacement', 'N/A'),
                        'jours': jours
                    })
        except:
            pass
    
    if stats['total'] > 0:
        stats['temps_moyen'] = round(jours_total / stats['total'], 1)
    
    stats['top_clients'] = dict(sorted(stats['top_clients'].items(), key=lambda x: x[1], reverse=True)[:5])
    
    return stats

def create_pie_chart(data, size=300):
    """Create pie chart"""
    drawing = Drawing(size, size)
    pie = Pie()
    pie.x = 30
    pie.y = 30
    pie.width = size - 60
    pie.height = size - 60
    pie.data = data
    
    colors_list = [
        colors.HexColor('#4ade80'),
        colors.HexColor('#60a5fa'),
        colors.HexColor('#facc15'),
        colors.HexColor('#ef4444')
    ]
    
    for i, color in enumerate(colors_list[:len(data)]):
        if i < len(pie.slices):
            pie.slices[i].fillColor = color
            pie.slices[i].strokeColor = colors.white
            pie.slices[i].strokeWidth = 2
    
    drawing.add(pie)
    return drawing

def create_bar_chart(labels, values):
    """Create bar chart"""
    drawing = Drawing(450, 250)
    bc = VerticalBarChart()
    bc.x = 50
    bc.y = 30
    bc.width = 350
    bc.height = 200
    bc.data = [values]
    bc.categoryAxis.categoryNames = [l[:12] for l in labels]
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = max(values) + 1 if values else 1
    
    bc.bars[0].fillColor = colors.HexColor('#fbbf24')
    bc.bars[0].strokeColor = colors.HexColor('#f59e0b')
    bc.bars[0].strokeWidth = 1
    
    drawing.add(bc)
    return drawing

def create_status_boxes(stats):
    """Create status indicator boxes"""
    drawing = Drawing(600, 100)
    
    # Box 1: Total
    rect1 = Rect(10, 50, 130, 50, fillColor=colors.HexColor('#f0fdf4'), strokeColor=colors.HexColor('#4ade80'), strokeWidth=2)
    drawing.add(rect1)
    drawing.add(String(75, 80, str(stats['total']), fontSize=24, fontName='Helvetica-Bold', textAnchor='middle'))
    drawing.add(String(75, 60, 'Total palettes', fontSize=9, textAnchor='middle'))
    
    # Box 2: Temps moyen
    rect2 = Rect(155, 50, 130, 50, fillColor=colors.HexColor('#eff6ff'), strokeColor=colors.HexColor('#60a5fa'), strokeWidth=2)
    drawing.add(rect2)
    drawing.add(String(220, 80, f"{stats['temps_moyen']}j", fontSize=24, fontName='Helvetica-Bold', textAnchor='middle'))
    drawing.add(String(220, 60, 'Temps moyen', fontSize=9, textAnchor='middle'))
    
    # Box 3: Urgentes
    rect3 = Rect(300, 50, 130, 50, fillColor=colors.HexColor('#fef2f2'), strokeColor=colors.HexColor('#ef4444'), strokeWidth=2)
    drawing.add(rect3)
    drawing.add(String(365, 80, str(len(stats['critiques'])), fontSize=24, fontName='Helvetica-Bold', textAnchor='middle', fillColor=colors.HexColor('#dc2626')))
    drawing.add(String(365, 60, 'Urgentes (+28j)', fontSize=9, textAnchor='middle'))
    
    # Box 4: Clients
    rect4 = Rect(445, 50, 130, 50, fillColor=colors.HexColor('#f5f3ff'), strokeColor=colors.HexColor('#a78bfa'), strokeWidth=2)
    drawing.add(rect4)
    drawing.add(String(510, 80, str(len(stats['top_clients'])), fontSize=24, fontName='Helvetica-Bold', textAnchor='middle'))
    drawing.add(String(510, 60, 'Clients', fontSize=9, textAnchor='middle'))
    
    return drawing

def generate_pdf(stats, filename='rapport_rack.pdf'):
    doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
    story = []
    styles = getSampleStyleSheet()
    
    # ===== PAGE 1 =====
    
    # Titre
    title_style = ParagraphStyle('title', parent=styles['Normal'], fontSize=32, fontName='Helvetica-Bold',
                                 textColor=colors.white, alignment=TA_CENTER)
    title_para = Paragraph("RAPPORT RACK AUEM", title_style)
    title_table = Table([[title_para]], colWidths=[19*cm])
    title_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1c1814')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(title_table)
    story.append(Spacer(1, 0.2*cm))
    
    # Date
    week_num = datetime.now().isocalendar()[1]
    year = datetime.now().year
    story.append(Paragraph(
        f"Semaine {week_num} - {year} | {datetime.now().strftime('%d/%m/%Y')}",
        ParagraphStyle('date', parent=styles['Normal'], fontSize=11, alignment=TA_CENTER, textColor=colors.HexColor('#666'))
    ))
    story.append(Spacer(1, 0.5*cm))
    
    # Boxes de stats
    story.append(create_status_boxes(stats))
    story.append(Spacer(1, 0.5*cm))
    
    # Titre section
    story.append(Paragraph("📊 RÉPARTITION PAR DÉLAI", ParagraphStyle('heading', parent=styles['Heading2'], fontSize=14, fontName='Helvetica-Bold')))
    story.append(Spacer(1, 0.3*cm))
    
    # Pie chart
    zone_values = [stats['par_zone']['vert'], stats['par_zone']['bleu'], 
                   stats['par_zone']['jaune'], stats['par_zone']['rouge']]
    if sum(zone_values) > 0:
        story.append(create_pie_chart(zone_values))
        story.append(Spacer(1, 0.2*cm))
    
    # Légende
    legend_data = [
        ['🟢 0-15 jours', f"{stats['par_zone']['vert']} ({round(100*stats['par_zone']['vert']/stats['total'], 1) if stats['total'] > 0 else 0}%)"],
        ['🔵 15-21 jours', f"{stats['par_zone']['bleu']} ({round(100*stats['par_zone']['bleu']/stats['total'], 1) if stats['total'] > 0 else 0}%)"],
        ['🟡 21-28 jours', f"{stats['par_zone']['jaune']} ({round(100*stats['par_zone']['jaune']/stats['total'], 1) if stats['total'] > 0 else 0}%)"],
        ['🔴 +28 jours', f"{stats['par_zone']['rouge']} ({round(100*stats['par_zone']['rouge']/stats['total'], 1) if stats['total'] > 0 else 0}%)"],
    ]
    legend_table = Table(legend_data, colWidths=[8*cm, 8*cm])
    legend_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(legend_table)
    story.append(Spacer(1, 0.5*cm))
    
    # ===== PAGE 2 =====
    story.append(PageBreak())
    
    # Top clients
    if stats['top_clients']:
        story.append(Paragraph("🏢 TOP 5 CLIENTS", ParagraphStyle('heading', parent=styles['Heading2'], fontSize=14, fontName='Helvetica-Bold')))
        story.append(Spacer(1, 0.3*cm))
        
        clients = list(stats['top_clients'].keys())
        values = list(stats['top_clients'].values())
        
        story.append(create_bar_chart(clients, values))
        story.append(Spacer(1, 0.3*cm))
        
        # Tableau détaillé
        clients_data = [['Rang', 'Client', 'Palettes', '%']]
        total_clients = sum(values)
        for idx, (client, count) in enumerate(stats['top_clients'].items(), 1):
            pct = round(100 * count / total_clients, 1) if total_clients > 0 else 0
            clients_data.append([str(idx), client[:20], str(count), f"{pct}%"])
        
        clients_table = Table(clients_data, colWidths=[1.5*cm, 10*cm, 2*cm, 2*cm])
        clients_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1c1814')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fafafa')]),
        ]))
        story.append(clients_table)
        story.append(Spacer(1, 0.5*cm))
    
    # Urgentes
    if stats['critiques']:
        story.append(Paragraph("🚨 À TRAITER IMMÉDIATEMENT", ParagraphStyle('heading', parent=styles['Heading2'], fontSize=14, fontName='Helvetica-Bold', textColor=colors.HexColor('#dc2626'))))
        story.append(Spacer(1, 0.3*cm))
        
        critical_data = [['Client', 'Emplacement', 'Jours', 'Délai dépassé']]
        for crit in stats['critiques']:
            delai_dep = crit['jours'] - 28
            critical_data.append([
                crit['client'][:20],
                crit['emplacement'],
                str(crit['jours']),
                f"+{delai_dep}j"
            ])
        
        critical_table = Table(critical_data, colWidths=[6*cm, 5*cm, 2*cm, 3*cm])
        critical_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc2626')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (3, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#fca5a5')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#fee2e2'), colors.HexColor('#fecaca')]),
        ]))
        story.append(critical_table)
    else:
        story.append(Paragraph(
            "✅ Aucune palette urgente! Tout est sous contrôle.",
            ParagraphStyle('success', parent=styles['Normal'], fontSize=12, textColor=colors.HexColor('#16a34a'), fontName='Helvetica-Bold')
        ))
    
    story.append(Spacer(1, 1*cm))
    
    # Footer
    story.append(Paragraph(
        f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
        ParagraphStyle('footer', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, textColor=colors.HexColor('#999'))
    ))
    
    doc.build(story)
    return filename

def send_email(pdf_filename, recipient_email):
    try:
        print(f"📧 Envoi à {recipient_email}...")
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"📊 Rapport Rack - Semaine {datetime.now().isocalendar()[1]}"
        msg['From'] = SMTP_USER
        msg['To'] = recipient_email
        msg['Date'] = formatdate(localtime=True)
        
        html = f"""
        <html><body style="font-family: Arial; color: #1c1814;">
            <h2>Rapport Rack AUEM</h2>
            <p>Semaine {datetime.now().isocalendar()[1]} - {datetime.now().year}</p>
            <p>Voir le PDF attaché pour le rapport complet avec graphiques et analyses.</p>
            <p style="color: #666; font-size: 12px;">Généré automatiquement chaque vendredi</p>
        </body></html>
        """
        
        msg.attach(MIMEText(html, 'html'))
        
        with open(pdf_filename, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename= {pdf_filename}')
            msg.attach(part)
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email envoyé!")
        return True
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    print("🚀 Génération du rapport rack")
    
    print("📥 Récupération des données...")
    data = fetch_firebase_data()
    palettes = parse_palettes(data)
    print(f"✅ {len(palettes)} palettes")
    
    print("📊 Calcul...")
    stats = calculate_stats(palettes)
    
    print("📄 PDF avec graphiques...")
    pdf_file = 'rapport_rack_hebdo.pdf'
    generate_pdf(stats, pdf_file)
    
    print("📧 Envoi...")
    if SMTP_PASSWORD == 'TON_APP_PASSWORD_ICI':
        print("❌ Change le mot de passe!")
        return
    
    send_email(pdf_file, RAPPORT_EMAIL)
    print("✅ Fait!")

if __name__ == '__main__':
    main()
