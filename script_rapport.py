#!/usr/bin/env python3
"""
AUEM Rack Weekly Report - ULTRA SIMPLE
Just numbers and essential info
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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
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
    doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm, leftMargin=2*cm, rightMargin=2*cm)
    story = []
    styles = getSampleStyleSheet()
    
    # ===== TITRE =====
    title = Paragraph(
        "RAPPORT RACK AUEM",
        ParagraphStyle('title', parent=styles['Normal'], fontSize=28, fontName='Helvetica-Bold', 
                      textColor=colors.HexColor('#1c1814'), alignment=TA_CENTER)
    )
    story.append(title)
    story.append(Spacer(1, 0.2*cm))
    
    # Date
    week_num = datetime.now().isocalendar()[1]
    year = datetime.now().year
    date_text = Paragraph(
        f"Semaine {week_num} - {year}",
        ParagraphStyle('date', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER, 
                      textColor=colors.HexColor('#666'))
    )
    story.append(date_text)
    story.append(Spacer(1, 0.8*cm))
    
    # ===== CHIFFRES CLÉS =====
    story.append(Paragraph("Chiffres clés", ParagraphStyle('heading', parent=styles['Normal'], fontSize=14, fontName='Helvetica-Bold')))
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph(
        f"Total palettes en attente : <b>{stats['total']}</b>",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.15*cm))
    
    story.append(Paragraph(
        f"Temps moyen d'attente : <b>{stats['temps_moyen']} jours</b>",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.15*cm))
    
    story.append(Paragraph(
        f"Palettes urgentes (+28j) : <b>{len(stats['critiques'])}</b>",
        ParagraphStyle('urgent', parent=styles['Normal'], textColor=colors.HexColor('#dc2626'))
    ))
    story.append(Spacer(1, 0.8*cm))
    
    # ===== RÉPARTITION PAR DÉLAI =====
    story.append(Paragraph("Répartition par délai", ParagraphStyle('heading', parent=styles['Normal'], fontSize=14, fontName='Helvetica-Bold')))
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph(
        f"🟢 0-15 jours : <b>{stats['par_zone']['vert']}</b> palettes",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.15*cm))
    
    story.append(Paragraph(
        f"🔵 15-21 jours : <b>{stats['par_zone']['bleu']}</b> palettes",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.15*cm))
    
    story.append(Paragraph(
        f"🟡 21-28 jours : <b>{stats['par_zone']['jaune']}</b> palettes",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.15*cm))
    
    story.append(Paragraph(
        f"🔴 +28 jours : <b>{stats['par_zone']['rouge']}</b> palettes",
        ParagraphStyle('urgent', parent=styles['Normal'], textColor=colors.HexColor('#dc2626'))
    ))
    story.append(Spacer(1, 0.8*cm))
    
    # ===== PALETTES URGENTES =====
    if stats['critiques']:
        story.append(Paragraph(
            "À traiter immédiatement",
            ParagraphStyle('heading', parent=styles['Normal'], fontSize=14, fontName='Helvetica-Bold', textColor=colors.HexColor('#dc2626'))
        ))
        story.append(Spacer(1, 0.3*cm))
        
        for crit in stats['critiques']:
            story.append(Paragraph(
                f"• {crit['client']} - {crit['emplacement']} ({crit['jours']} jours)",
                styles['Normal']
            ))
            story.append(Spacer(1, 0.1*cm))
    else:
        story.append(Paragraph(
            "✅ Aucune palette urgente",
            ParagraphStyle('success', parent=styles['Normal'], fontSize=12, textColor=colors.HexColor('#16a34a'), fontName='Helvetica-Bold')
        ))
    
    story.append(Spacer(1, 1*cm))
    
    # Footer
    footer = Paragraph(
        f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
        ParagraphStyle('footer', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, textColor=colors.HexColor('#999'))
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
    
    print("📄 PDF...")
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
