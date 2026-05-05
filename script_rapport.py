#!/usr/bin/env python3
"""
AUEM Rack Weekly Report - SIMPLE VERSION
Clear, minimal, easy to understand
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
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# ============================================================
# 🔧 CONFIGURATION - METS TES INFOS ICI
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
        'critiques': []
    }
    
    jours_total = 0
    
    for palette in palettes:
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
                        'client': palette.get('client', 'N/A'),
                        'emplacement': palette.get('emplacement', 'N/A'),
                        'jours': jours
                    })
        except:
            pass
    
    if stats['total'] > 0:
        stats['temps_moyen'] = round(jours_total / stats['total'], 1)
    
    return stats

def generate_pdf(stats, filename='rapport_rack.pdf'):
    doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
    story = []
    styles = getSampleStyleSheet()
    
    # Couleurs
    header_color = colors.HexColor('#1c1814')
    primary_color = colors.HexColor('#fbbf24')
    
    # ===== TITRE =====
    title = Paragraph(
        "RAPPORT RACK AUEM",
        ParagraphStyle('title', parent=styles['Normal'], fontSize=24, fontName='Helvetica-Bold', 
                      textColor=colors.white, alignment=TA_CENTER)
    )
    title_table = Table([[title]], colWidths=[19*cm])
    title_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), header_color),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(title_table)
    story.append(Spacer(1, 0.3*cm))
    
    # Date
    week_num = datetime.now().isocalendar()[1]
    year = datetime.now().year
    date_text = Paragraph(
        f"Semaine {week_num} - {year} | {datetime.now().strftime('%d/%m/%Y')}",
        ParagraphStyle('date', parent=styles['Normal'], fontSize=11, alignment=TA_CENTER, 
                      textColor=header_color)
    )
    story.append(date_text)
    story.append(Spacer(1, 0.5*cm))
    
    # ===== LES 4 CHIFFRES CLÉS =====
    story.append(Paragraph("📊 CHIFFRES CLÉS", styles['Heading2']))
    story.append(Spacer(1, 0.2*cm))
    
    key_data = [
        ['Total palettes', str(stats['total'])],
        ['Temps moyen d\'attente', f"{stats['temps_moyen']} jours"],
        ['Palettes urgentes (+28j)', str(len(stats['critiques']))],
    ]
    
    key_table = Table(key_data, colWidths=[10*cm, 6*cm])
    key_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 0), (1, -1), 14),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, primary_color),
    ]))
    story.append(key_table)
    story.append(Spacer(1, 0.5*cm))
    
    # ===== RÉPARTITION PAR DÉLAI =====
    story.append(Paragraph("⏱️ RÉPARTITION PAR DÉLAI", styles['Heading2']))
    story.append(Spacer(1, 0.2*cm))
    
    zone_data = [
        ['Délai', 'Nombre', ''],
        ['🟢 0-15 jours', str(stats['par_zone']['vert']), ''],
        ['🔵 15-21 jours', str(stats['par_zone']['bleu']), ''],
        ['🟡 21-28 jours', str(stats['par_zone']['jaune']), ''],
        ['🔴 +28 jours (URGENT)', str(stats['par_zone']['rouge']), '⚠️'],
    ]
    
    zone_table = Table(zone_data, colWidths=[8*cm, 3*cm, 6*cm])
    zone_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), header_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 0), (1, -1), 12),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ]))
    story.append(zone_table)
    story.append(Spacer(1, 0.5*cm))
    
    # ===== PALETTES URGENTES =====
    if stats['critiques']:
        story.append(Paragraph("🚨 PALETTES À TRAITER IMMÉDIATEMENT", styles['Heading2']))
        story.append(Spacer(1, 0.2*cm))
        
        critical_data = [['Client', 'Emplacement', 'Jours']]
        for crit in stats['critiques']:
            critical_data.append([
                crit['client'][:20],
                crit['emplacement'],
                str(crit['jours'])
            ])
        
        critical_table = Table(critical_data, colWidths=[6*cm, 6*cm, 3*cm])
        critical_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc2626')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (2, 0), (2, -1), 11),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#fca5a5')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#fee2e2'), colors.HexColor('#fecaca')]),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fef2f2')),
        ]))
        story.append(critical_table)
    else:
        story.append(Paragraph(
            "✅ Aucune palette urgente! Tout est sous contrôle.",
            ParagraphStyle('success', parent=styles['Normal'], fontSize=12, 
                          textColor=colors.HexColor('#16a34a'), fontName='Helvetica-Bold')
        ))
    
    story.append(Spacer(1, 1*cm))
    
    # Footer
    footer = Paragraph(
        f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
        ParagraphStyle('footer', parent=styles['Normal'], fontSize=9, 
                      alignment=TA_CENTER, textColor=colors.grey)
    )
    story.append(footer)
    
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
            <p>Voir le PDF attaché pour le rapport complet.</p>
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
        
        print(f"✅ Email envoyé avec succès!")
        return True
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    print("=" * 50)
    print("🚀 Génération du rapport rack")
    print("=" * 50)
    
    print("\n📥 Récupération des données...")
    data = fetch_firebase_data()
    palettes = parse_palettes(data)
    print(f"✅ {len(palettes)} palettes trouvées")
    
    print("\n📊 Calcul des stats...")
    stats = calculate_stats(palettes)
    
    print("\n📄 Génération du PDF...")
    pdf_file = 'rapport_rack_hebdo.pdf'
    generate_pdf(stats, pdf_file)
    print(f"✅ PDF créé")
    
    print("\n📧 Envoi de l'email...")
    if SMTP_PASSWORD == 'TON_APP_PASSWORD_ICI':
        print("❌ Change le mot de passe dans le script!")
        return
    
    send_email(pdf_file, RAPPORT_EMAIL)
    
    print("\n" + "=" * 50)
    print("✅ Rapport généré avec succès!")
    print("=" * 50)

if __name__ == '__main__':
    main()
