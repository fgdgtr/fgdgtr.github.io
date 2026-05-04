#!/usr/bin/env python3
"""
AUEM Rack Weekly Report Generator
Reads Firebase data and generates PDF report
"""

import json
import smtplib
import os
from datetime import datetime, timedelta
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
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Configuration
FIREBASE_URL = os.getenv('FIREBASE_URL', 'https://auem-rac-default-rtdb.europe-west1.firebasedatabase.app/retour.json')
SMTP_USER = os.getenv('SMTP_USER', 'axefoxe8592@gmail.com')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', 'xsmtpsib-1386a13c39dbb774792056d8212d82efc25706197bb9d853f9a8aeabe4f92923-QEWZbJQsl6z90NCo')
RAPPORT_EMAIL = os.getenv('RAPPORT_EMAIL', 'axefoxe8592@gmail.com')
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

def fetch_firebase_data():
    """Fetch data from Firebase"""
    try:
        response = requests.get(FIREBASE_URL)
        data = response.json()
        return data if data else {}
    except Exception as e:
        print(f"Erreur Firebase: {e}")
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

def generate_pdf(stats, filename='rapport_rack.pdf'):
    """Generate PDF report"""
    doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1c1814'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1c1814'),
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold',
        borderColor=colors.HexColor('#fbbf24'),
        borderWidth=2,
        borderPadding=4
    )
    
    # Title
    week_num = datetime.now().isocalendar()[1]
    year = datetime.now().year
    story.append(Paragraph(f"📊 RAPPORT RACK HEBDOMADAIRE", title_style))
    story.append(Paragraph(f"Semaine {week_num} - {year}", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    # Statistics section
    story.append(Paragraph("📈 STATISTIQUES GLOBALES", heading_style))
    
    stats_data = [
        ['Métrique', 'Valeur'],
        ['Total palettes en attente', str(stats['total'])],
        ['Temps d\'attente moyen (jours)', str(stats['temps_moyen'])],
        ['Palettes critiques (>28j)', str(len(stats['critiques']))]
    ]
    
    stats_table = Table(stats_data, colWidths=[10*cm, 5*cm])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1c1814')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f3efe9')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5dfd6')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#faf7f3')])
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 0.5*cm))
    
    # Zones section
    story.append(Paragraph("🎯 PALETTES PAR ZONE DÉLAI", heading_style))
    
    zones_data = [
        ['Zone', 'Délai', 'Quantité'],
        ['🟢', '0-15 jours', str(stats['par_zone']['vert'])],
        ['🔵', '15-21 jours', str(stats['par_zone']['bleu'])],
        ['🟡', '21-28 jours', str(stats['par_zone']['jaune'])],
        ['🔴', '+28 jours (CRITIQUE)', str(stats['par_zone']['rouge'])]
    ]
    
    zones_table = Table(zones_data, colWidths=[2*cm, 8*cm, 5*cm])
    zones_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1c1814')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f3efe9')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5dfd6')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#faf7f3')])
    ]))
    story.append(zones_table)
    story.append(Spacer(1, 0.5*cm))
    
    # Top clients
    if stats['top_clients']:
        story.append(Paragraph("🏢 TOP 5 CLIENTS", heading_style))
        
        clients_data = [['Rang', 'Client', 'Palettes']]
        for idx, (client, count) in enumerate(stats['top_clients'].items(), 1):
            clients_data.append([str(idx), client, str(count)])
        
        clients_table = Table(clients_data, colWidths=[2*cm, 10*cm, 3*cm])
        clients_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1c1814')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f3efe9')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5dfd6')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#faf7f3')])
        ]))
        story.append(clients_table)
        story.append(Spacer(1, 0.5*cm))
    
    # Critical palettes
    if stats['critiques']:
        story.append(Paragraph("🚨 À TRAITER URGEMMENT (>28j)", heading_style))
        
        critical_data = [['Client', 'Emplacement', 'Jours']]
        for crit in stats['critiques']:
            critical_data.append([crit['client'], crit['palette'], str(crit['jours'])])
        
        critical_table = Table(critical_data, colWidths=[6*cm, 6*cm, 3*cm])
        critical_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc2626')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fef2f2')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#fca5a5')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#fef2f2'), colors.HexColor('#fee2e2')])
        ]))
        story.append(critical_table)
    
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", styles['Normal']))
    
    doc.build(story)
    return filename

def send_email(pdf_filename, recipient_email):
    """Send PDF by email"""
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"📊 Rapport Rack Hebdomadaire - Semaine {datetime.now().isocalendar()[1]}"
        msg['From'] = SMTP_USER
        msg['To'] = recipient_email
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = f'<{datetime.now().timestamp()}@auem.fr>'
        msg['X-Mailer'] = 'AUEM Rack Report Generator'
        
        # HTML body
        html = f"""
        <html>
        <head></head>
        <body style="font-family: Arial, sans-serif; color: #1c1814; background-color: #f3efe9;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #1c1814; color: #f3efe9; padding: 20px; border-radius: 10px; text-align: center;">
                    <h1 style="margin: 0; font-size: 24px;">📊 RAPPORT RACK HEBDOMADAIRE</h1>
                    <p style="margin: 5px 0 0 0; font-size: 14px;">Semaine {datetime.now().isocalendar()[1]} - {datetime.now().year}</p>
                </div>
                
                <div style="background-color: white; padding: 20px; margin-top: 10px; border-radius: 10px; border: 1px solid #e5dfd6;">
                    <p>Bonjour,</p>
                    <p>Veuillez trouver ci-joint le <strong>rapport hebdomadaire du rack AUEM</strong>.</p>
                    
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
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email envoyé à {recipient_email}")
        return True
    
    except Exception as e:
        print(f"❌ Erreur d'envoi: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Génération du rapport hebdomadaire...")
    
    # Fetch data
    data = fetch_firebase_data()
    palettes = parse_palettes(data)
    
    if not palettes:
        print("⚠️ Aucune donnée trouvée")
        palettes = []
    
    print(f"📦 {len(palettes)} palettes trouvées")
    
    # Calculate stats
    stats = calculate_stats(palettes)
    print(f"📊 Stats calculées: {stats['total']} palettes, {stats['temps_moyen']}j en moyenne")
    
    # Generate PDF
    pdf_file = 'rapport_rack_hebdo.pdf'
    generate_pdf(stats, pdf_file)
    print(f"📄 PDF généré: {pdf_file}")
    
    # Send email
    if SMTP_PASSWORD and RAPPORT_EMAIL:
        send_email(pdf_file, RAPPORT_EMAIL)
    else:
        print("⚠️ Email non configuré (variables manquantes)")
    
    print("✅ Rapport hebdomadaire généré avec succès!")

if __name__ == '__main__':
    main()
