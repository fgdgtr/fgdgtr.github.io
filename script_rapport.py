#!/usr/bin/env python3
"""
AUEM Rack Weekly Report - PALETTES avec DÉLAI EN ROUGE
Focus on palettes with red alert for overdue deliveries
"""

import smtplib
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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

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
                    'emplacement': value.get('emplacement', 'N/A'),
                    'date_entree': value.get('date_entree', 'N/A'),
                    'afs': value.get('afs', 'N/A'),
                })
    return palettes

def calculate_stats(palettes):
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    
    stats = {
        'par_zone': {
            'hors_production': 0,
            '0_15': 0,
            '15_21': 0,
            '21_28': 0,
            'plus_28': 0
        },
        'arrivees_semaine': 0,
        'total': len(palettes),
        'details_urgentes': [],
        'details_zone': {
            'hors_production': [],
            '0_15': [],
            '15_21': [],
            '21_28': [],
            'plus_28': []
        }
    }
    
    for palette in palettes:
        try:
            date_str = palette.get('date_entree', '')
            
            # Vérifier si c'est hors production (sans date)
            if not date_str or date_str == 'N/A':
                stats['par_zone']['hors_production'] += 1
                stats['details_zone']['hors_production'].append(palette)
                continue
            
            if len(date_str) >= 10:
                date_entree = datetime.strptime(date_str[:10], '%Y-%m-%d')
                jours = (today - date_entree).days
                
                # Compter les arrivées de cette semaine
                if date_entree >= week_start:
                    stats['arrivees_semaine'] += 1
                
                # Classer par zone
                if jours <= 15:
                    stats['par_zone']['0_15'] += 1
                    stats['details_zone']['0_15'].append((palette, jours))
                elif jours <= 21:
                    stats['par_zone']['15_21'] += 1
                    stats['details_zone']['15_21'].append((palette, jours))
                elif jours <= 28:
                    stats['par_zone']['21_28'] += 1
                    stats['details_zone']['21_28'].append((palette, jours))
                else:
                    stats['par_zone']['plus_28'] += 1
                    stats['details_zone']['plus_28'].append((palette, jours))
                    stats['details_urgentes'].append((palette, jours))
        except:
            pass
    
    return stats

def generate_pdf(stats, filename='rapport_rack.pdf'):
    doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm, leftMargin=1*cm, rightMargin=1*cm)
    story = []
    styles = getSampleStyleSheet()
    
    # ===== TITRE =====
    title_style = ParagraphStyle('title', parent=styles['Normal'], fontSize=32, fontName='Helvetica-Bold',
                                 textColor=colors.white, alignment=TA_CENTER)
    title_para = Paragraph("RAPPORT RACK AUEM", title_style)
    title_table = Table([[title_para]], colWidths=[18*cm])
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
    story.append(Spacer(1, 0.4*cm))
    
    # ===== STATS ARRIVÉES/SORTIES =====
    story.append(Paragraph("📥 MOUVEMENTS CETTE SEMAINE", ParagraphStyle('heading', parent=styles['Heading2'], fontSize=12, fontName='Helvetica-Bold')))
    story.append(Spacer(1, 0.2*cm))
    
    movements_data = [
        ['Palettes arrivées cette semaine', f"<b>{stats['arrivees_semaine']}</b>"],
        ['Total palettes en attente', f"<b>{stats['total']}</b>"],
        ['Palettes urgentes (+28j)', f"<b>{stats['par_zone']['plus_28']}</b>"],
    ]
    
    movements_table = Table(movements_data, colWidths=[10*cm, 6*cm])
    movements_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 0), (1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#fafafa'), colors.HexColor('#fff3cd')])
    ]))
    story.append(movements_table)
    story.append(Spacer(1, 0.5*cm))
    
    # ===== TABLEAU PRINCIPAL DES ZONES =====
    story.append(Paragraph("📊 RÉPARTITION DES PALETTES", ParagraphStyle('heading', parent=styles['Heading2'], fontSize=12, fontName='Helvetica-Bold')))
    story.append(Spacer(1, 0.2*cm))
    
    zone_data = [
        ['Type de palette', 'Quantité', '%', 'Emplacements'],
        ['Hors production', str(stats['par_zone']['hors_production']), 
         f"{round(100*stats['par_zone']['hors_production']/stats['total'], 1) if stats['total'] > 0 else 0}%", 
         f"{' | '.join([p.get('emplacement', 'N/A') for p in stats['details_zone']['hors_production'][:3]])}" if stats['details_zone']['hors_production'] else '-'],
        ['🟢 0-15 jours', str(stats['par_zone']['0_15']), 
         f"{round(100*stats['par_zone']['0_15']/stats['total'], 1) if stats['total'] > 0 else 0}%", 
         f"{' | '.join([p[0].get('emplacement', 'N/A') for p in stats['details_zone']['0_15'][:3]])}" if stats['details_zone']['0_15'] else '-'],
        ['🔵 15-21 jours', str(stats['par_zone']['15_21']), 
         f"{round(100*stats['par_zone']['15_21']/stats['total'], 1) if stats['total'] > 0 else 0}%", 
         f"{' | '.join([p[0].get('emplacement', 'N/A') for p in stats['details_zone']['15_21'][:3]])}" if stats['details_zone']['15_21'] else '-'],
        ['🟡 21-28 jours', str(stats['par_zone']['21_28']), 
         f"{round(100*stats['par_zone']['21_28']/stats['total'], 1) if stats['total'] > 0 else 0}%", 
         f"{' | '.join([p[0].get('emplacement', 'N/A') for p in stats['details_zone']['21_28'][:3]])}" if stats['details_zone']['21_28'] else '-'],
        ['🔴 +28 jours', str(stats['par_zone']['plus_28']), 
         f"{round(100*stats['par_zone']['plus_28']/stats['total'], 1) if stats['total'] > 0 else 0}%", 
         f"{' | '.join([p[0].get('emplacement', 'N/A') for p in stats['details_zone']['plus_28'][:3]])} ⚠️ DÉLAI DÉPASSÉ" if stats['details_zone']['plus_28'] else '-'],
    ]
    
    zone_table = Table(zone_data, colWidths=[6*cm, 1.5*cm, 1.5*cm, 8*cm])
    zone_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1c1814')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (0, 1), (2, 4), 'CENTER'),
        ('ALIGN', (3, 1), (3, -1), 'LEFT'),
        ('FONTSIZE', (1, 1), (1, -1), 12),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (3, 1), (3, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1.5, colors.HexColor('#e0e0e0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, 4), [colors.white, colors.HexColor('#f9f9f9')]),
        ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#fee2e2')),
        ('TEXTCOLOR', (3, 5), (3, 5), colors.HexColor('#dc2626')),
        ('FONTNAME', (3, 5), (3, 5), 'Helvetica-Bold'),
    ]))
    story.append(zone_table)
    story.append(Spacer(1, 0.5*cm))
    
    # ===== PAGE 2: PALETTES URGENTES EN DÉTAIL =====
    if stats['details_urgentes']:
        story.append(PageBreak())
        story.append(Paragraph("🚨 PALETTES URGENTES À TRAITER", 
                             ParagraphStyle('heading', parent=styles['Heading2'], fontSize=12, fontName='Helvetica-Bold', textColor=colors.HexColor('#dc2626'))))
        story.append(Spacer(1, 0.2*cm))
        
        urgent_data = [['⚠️ EMPLACEMENT', 'Client', 'Jours', 'DÉLAI DÉPASSÉ DE']]
        for palette, jours in stats['details_urgentes']:
            delai_dep = jours - 28
            urgent_data.append([
                palette.get('emplacement', 'N/A'),
                palette.get('client', 'N/A')[:15],
                str(jours),
                f"+{delai_dep}j"
            ])
        
        urgent_table = Table(urgent_data, colWidths=[4*cm, 6*cm, 2*cm, 4*cm])
        urgent_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc2626')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 1), (0, -1), colors.HexColor('#dc2626')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#fca5a5')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#fee2e2'), colors.HexColor('#fecaca')]),
        ]))
        story.append(urgent_table)
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
            <p>Voir le PDF attaché pour le rapport complet avec les mouvements de palettes.</p>
            <p style="color: #dc2626; font-weight: bold;">⚠️ Les palettes avec délai dépassé sont marquées en ROUGE!</p>
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
EOF
