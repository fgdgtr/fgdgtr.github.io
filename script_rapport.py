#!/usr/bin/env python3
"""
AUEM Rack Weekly Report Generator - BEAUTIFUL VERSION
With colors, charts and professional design
"""

import json
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
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.widgets.markers import makeMarker
import io

# ============================================================
# 🔧 CONFIGURATION - METS TES INFOS ICI
# ============================================================

FIREBASE_URL = 'https://auem-rac-default-rtdb.europe-west1.firebasedatabase.app/retour.json'

# Email à utiliser pour envoyer
SMTP_USER = 'k61587549@gmail.com' 
SMTP_PASSWORD = 'gnpe bpxy ljpx slib'  

# Email qui reçoit le rapport 
RAPPORT_EMAIL = 'axefoxe8592@gmail.com' 

# Serveur SMTP Gmail
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

# ============================================================
# COULEURS AUEM
# ============================================================
COULEUR_HEADER = colors.HexColor('#1c1814')
COULEUR_PRIMARY = colors.HexColor('#fbbf24')
COULEUR_BG = colors.HexColor('#f3efe9')
COULEUR_VERT = colors.HexColor('#4ade80')
COULEUR_BLEU = colors.HexColor('#60a5fa')
COULEUR_JAUNE = colors.HexColor('#facc15')
COULEUR_ROUGE = colors.HexColor('#ef4444')

# ============================================================

def fetch_firebase_data():
    """Fetch data from Firebase"""
    try:
        response = requests.get(FIREBASE_URL)
        data = response.json()
        return data if data else {}
    except Exception as e:
        print(f"❌ Erreur Firebase: {e}")
        return {}

def parse_palettes(data):
    """Parse palette data from Firebase"""
    palettes = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                palette = {
                    'id': key,
                    'client': value.get('client', 'N/A'),
                    'afs': value.get('afs', 'N/A'),
                    'date_entree': value.get('date_entree', 'N/A'),
                    'emplacement': value.get('emplacement', 'N/A'),
                    'reste_place': value.get('reste_place', 'N/A')
                }
                palettes.append(palette)
    
    return palettes

def calculate_stats(palettes):
    """Calculate statistics from palettes"""
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
        
        # Count client
        stats['top_clients'][client] = stats['top_clients'].get(client, 0) + 1
        
        # Try to calculate days
        try:
            date_str = palette.get('date_entree', '')
            if date_str and len(date_str) >= 10:
                date_entree = datetime.strptime(date_str[:10], '%Y-%m-%d')
                jours = (today - date_entree).days
                jours_total += jours
                
                # Zone color
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
                        'palette': palette.get('emplacement', 'N/A'),
                        'jours': jours
                    })
        except:
            pass
    
    if stats['total'] > 0:
        stats['temps_moyen'] = round(jours_total / stats['total'], 1)
    
    # Top 5 clients
    stats['top_clients'] = dict(sorted(stats['top_clients'].items(), key=lambda x: x[1], reverse=True)[:5])
    
    return stats

def create_pie_chart(data, title):
    """Create a pie chart"""
    drawing = Drawing(400, 250)
    pie = Pie()
    pie.x = 50
    pie.y = 50
    pie.width = 300
    pie.height = 200
    pie.data = data
    pie.labels = [f"{int(v)} palettes" for v in data]
    pie.slices.strokeWidth = 0
    
    # Couleurs
    colors_list = [COULEUR_VERT, COULEUR_BLEU, COULEUR_JAUNE, COULEUR_ROUGE]
    for i, color in enumerate(colors_list[:len(data)]):
        if i < len(pie.slices):
            pie.slices[i].fillColor = color
    
    drawing.add(pie)
    return drawing

def create_bar_chart(clients, values):
    """Create a bar chart"""
    drawing = Drawing(400, 250)
    bc = VerticalBarChart()
    bc.x = 50
    bc.y = 30
    bc.width = 300
    bc.height = 200
    bc.data = [values]
    bc.categoryAxis.categoryNames = [c[:15] for c in clients]
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = max(values) + 1 if values else 1
    
    # Couleur des barres
    bc.bars[0].fillColor = COULEUR_PRIMARY
    
    drawing.add(bc)
    return drawing

def generate_pdf(stats, filename='rapport_rack.pdf'):
    """Generate beautiful PDF report"""
    doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=0.8*cm, bottomMargin=0.8*cm)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.white,
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=COULEUR_HEADER,
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold',
        borderColor=COULEUR_PRIMARY,
        borderWidth=3,
        borderPadding=6
    )
    
    # ===== PAGE 1 =====
    
    # Header avec fond coloré
    header_table = Table([
        [Paragraph(f"📊 RAPPORT RACK AUEM", title_style)]
    ], colWidths=[19*cm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COULEUR_HEADER),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.3*cm))
    
    # Sous-titre
    week_num = datetime.now().isocalendar()[1]
    year = datetime.now().year
    subtitle = Paragraph(
        f"<b>Semaine {week_num} - {year}</b> | {datetime.now().strftime('%d/%m/%Y')}",
        ParagraphStyle('subtitle', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER, textColor=COULEUR_HEADER)
    )
    story.append(subtitle)
    story.append(Spacer(1, 0.5*cm))
    
    # ===== STATISTIQUES GLOBALES =====
    story.append(Paragraph("📈 STATISTIQUES GLOBALES", heading_style))
    
    # Créer 4 petites boîtes de stats
    stats_data = [
        ['Total\nPalettes', 'Temps Moyen\nd\'Attente', 'Palettes\nCritiques', 'Clients\nUniques'],
        [
            str(stats['total']),
            f"{stats['temps_moyen']} j",
            str(len(stats['critiques'])),
            str(len(stats['top_clients']))
        ]
    ]
    
    stats_table = Table(stats_data, colWidths=[4.5*cm, 4.5*cm, 4.5*cm, 4.5*cm])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COULEUR_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, 1), 16),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('TOPPADDING', (0, 1), (-1, 1), 15),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 15),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#faf7f3')),
        ('GRID', (0, 0), (-1, -1), 1, COULEUR_PRIMARY),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [COULEUR_HEADER, colors.HexColor('#faf7f3')])
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 0.5*cm))
    
    # ===== GRAPHIQUE CAMEMBERT =====
    story.append(Paragraph("🎯 RÉPARTITION PAR DÉLAI", heading_style))
    
    zone_values = [
        stats['par_zone']['vert'],
        stats['par_zone']['bleu'],
        stats['par_zone']['jaune'],
        stats['par_zone']['rouge']
    ]
    
    if sum(zone_values) > 0:
        pie_drawing = create_pie_chart(zone_values, "Zones")
        story.append(pie_drawing)
        story.append(Spacer(1, 0.3*cm))
        
        # Légende
        legend_data = [
            ['🟢 0-15 jours', f"{stats['par_zone']['vert']} palettes"],
            ['🔵 15-21 jours', f"{stats['par_zone']['bleu']} palettes"],
            ['🟡 21-28 jours', f"{stats['par_zone']['jaune']} palettes"],
            ['🔴 +28 jours', f"{stats['par_zone']['rouge']} palettes"]
        ]
        
        legend_table = Table(legend_data, colWidths=[8*cm, 8*cm])
        legend_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5dfd6')),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#faf7f3')])
        ]))
        story.append(legend_table)
    
    story.append(Spacer(1, 0.5*cm))
    
    # ===== PAGE 2 =====
    story.append(PageBreak())
    
    # ===== TOP CLIENTS =====
    if stats['top_clients']:
        story.append(Paragraph("🏢 TOP 5 CLIENTS", heading_style))
        
        clients = list(stats['top_clients'].keys())
        values = list(stats['top_clients'].values())
        
        bar_drawing = create_bar_chart(clients, values)
        story.append(bar_drawing)
        story.append(Spacer(1, 0.3*cm))
        
        # Tableau détaillé
        clients_data = [['Rang', 'Client', 'Palettes']]
        for idx, (client, count) in enumerate(stats['top_clients'].items(), 1):
            clients_data.append([str(idx), client, str(count)])
        
        clients_table = Table(clients_data, colWidths=[2*cm, 12*cm, 3*cm])
        clients_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COULEUR_HEADER),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#faf7f3')),
            ('GRID', (0, 0), (-1, -1), 1, COULEUR_PRIMARY),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fef3c7')])
        ]))
        story.append(clients_table)
        story.append(Spacer(1, 0.5*cm))
    
    # ===== PALETTES CRITIQUES =====
    if stats['critiques']:
        story.append(Paragraph("🚨 À TRAITER URGEMMENT (+28j)", heading_style))
        
        critical_data = [['Client', 'Emplacement', 'Jours']]
        for crit in stats['critiques']:
            critical_data.append([crit['client'], crit['palette'], str(crit['jours'])])
        
        critical_table = Table(critical_data, colWidths=[6*cm, 6*cm, 3*cm])
        critical_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COULEUR_ROUGE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fef2f2')),
            ('GRID', (0, 0), (-1, -1), 1, COULEUR_ROUGE),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fee2e2')])
        ]))
        story.append(critical_table)
        story.append(Spacer(1, 0.5*cm))
    else:
        story.append(Paragraph(
            "✅ Aucune palette critique! Tout est en attente normale.",
            ParagraphStyle('success', parent=styles['Normal'], fontSize=11, textColor=COULEUR_VERT)
        ))
        story.append(Spacer(1, 0.5*cm))
    
    # ===== FOOTER =====
    story.append(Spacer(1, 1*cm))
    footer_text = f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} | AUEM Rack Management System"
    story.append(Paragraph(
        footer_text,
        ParagraphStyle('footer', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, textColor=colors.HexColor('#aba49d'))
    ))
    
    doc.build(story)
    return filename

def send_email(pdf_filename, recipient_email):
    """Send PDF by email"""
    try:
        print(f"📧 Tentative d'envoi à {recipient_email}...")
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"📊 Rapport Rack Hebdomadaire - Semaine {datetime.now().isocalendar()[1]}"
        msg['From'] = SMTP_USER
        msg['To'] = recipient_email
        msg['Date'] = formatdate(localtime=True)
        
        # HTML body
        html = f"""
        <html>
        <head></head>
        <body style="font-family: Arial, sans-serif; color: #1c1814; background-color: #f3efe9;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #1c1814; color: #f3efe9; padding: 20px; border-radius: 10px; text-align: center;">
                    <h1 style="margin: 0; font-size: 24px;">📊 RAPPORT RACK AUEM</h1>
                    <p style="margin: 5px 0 0 0; font-size: 14px;">Semaine {datetime.now().isocalendar()[1]} - {datetime.now().year}</p>
                </div>
                
                <div style="background-color: white; padding: 20px; margin-top: 10px; border-radius: 10px; border: 1px solid #e5dfd6;">
                    <p>Bonjour,</p>
                    <p>Veuillez trouver ci-joint le <strong>rapport hebdomadaire du rack AUEM</strong> avec graphiques et analyses.</p>
                    
                    <div style="background-color: #fef3c7; border-left: 4px solid #fbbf24; padding: 15px; margin: 15px 0; border-radius: 5px;">
                        <p style="margin: 0;"><strong>⚠️ Rappel important :</strong> Consultez la section "À traiter urgemment" pour les palettes en attente depuis plus de 28 jours.</p>
                    </div>
                    
                    <p>Ce rapport est généré automatiquement chaque vendredi à 17h.</p>
                    <p style="color: #6e6560; font-size: 12px;">AUEM Rack Management System</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html, 'html'))
        
        # Attach PDF
        with open(pdf_filename, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename= {pdf_filename}')
            msg.attach(part)
        
        # Send
        print(f"📡 Connexion à {SMTP_SERVER}:{SMTP_PORT}...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        print(f"🔐 Authentification...")
        server.login(SMTP_USER, SMTP_PASSWORD)
        print(f"✉️ Envoi du message...")
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email envoyé à {recipient_email} avec succès!")
        return True
    
    except Exception as e:
        print(f"❌ Erreur d'envoi: {e}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("🚀 AUEM RACK - Génération du rapport hebdomadaire")
    print("=" * 60)
    
    # Fetch data
    print("\n📥 Récupération des données Firebase...")
    data = fetch_firebase_data()
    palettes = parse_palettes(data)
    print(f"✅ {len(palettes)} palettes trouvées")
    
    # Calculate stats
    print("\n📊 Calcul des statistiques...")
    stats = calculate_stats(palettes)
    print(f"✅ Total: {stats['total']} palettes")
    print(f"✅ Temps moyen: {stats['temps_moyen']} jours")
    print(f"✅ Critiques (+28j): {len(stats['critiques'])}")
    
    # Generate PDF
    print("\n📄 Génération du PDF avec graphiques...")
    pdf_file = 'rapport_rack_hebdo.pdf'
    generate_pdf(stats, pdf_file)
    print(f"✅ PDF créé: {pdf_file}")
    
    # Send email
    print("\n📧 Envoi de l'email...")
    if SMTP_PASSWORD == 'TON_APP_PASSWORD_ICI':
        print("❌ ERREUR: Tu n'as pas changé le mot de passe dans le script!")
        print("   Change SMTP_PASSWORD dans le fichier!")
        return
    
    send_email(pdf_file, RAPPORT_EMAIL)
    
    print("\n" + "=" * 60)
    print("✅ Rapport hebdomadaire généré avec succès!")
    print("=" * 60)

if __name__ == '__main__':
    main()
