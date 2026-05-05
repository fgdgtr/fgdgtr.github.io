#!/usr/bin/env python3
"""
AUEM Rack Weekly Report
Structure Firebase réelle :
{
  "A1": { "colis": [ { "client": "...", "company": "...", "arc": "...", "afs": [...], "ts": 1234567890000, "hors_prod": false, "done": false } ] },
  "B3": { "colis": [ ... ] },
  ...
}
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
# CONFIGURATION
# ============================================================

FIREBASE_URL  = 'https://auem-rac-default-rtdb.europe-west1.firebasedatabase.app/retour.json'
SMTP_USER     = 'k61587549@gmail.com'
SMTP_PASSWORD = 'gnpe bpxy ljpx slib'
RAPPORT_EMAIL = 'axefoxe8592@gmail.com'
SMTP_SERVER   = 'smtp.gmail.com'
SMTP_PORT     = 587

# ============================================================


def fetch_firebase_data():
    try:
        response = requests.get(FIREBASE_URL)
        data = response.json()
        return data if data else {}
    except Exception as e:
        print(f"Erreur Firebase: {e}")
        return {}


def parse_palettes(data):
    """
    data = { "A1": { "colis": [...] }, "B2": { "colis": [...] }, ... }
    Retourne une liste de dicts avec le champ 'emplacement' injecte depuis la cle Firebase.
    """
    palettes = []
    if not isinstance(data, dict):
        return palettes

    for emplacement, value in data.items():
        if not isinstance(value, dict):
            continue
        colis_list = value.get('colis', [])
        if not isinstance(colis_list, list):
            continue
        for colis in colis_list:
            if not isinstance(colis, dict):
                continue
            # On ignore les colis marques comme retires
            if colis.get('done', False):
                continue

            # ts est en millisecondes (JavaScript Date.now())
            ts_ms = colis.get('ts')
            date_entree = None
            if ts_ms and isinstance(ts_ms, (int, float)) and ts_ms > 0:
                try:
                    date_entree = datetime.fromtimestamp(ts_ms / 1000)
                except Exception:
                    date_entree = None

            palettes.append({
                'emplacement': emplacement,
                'client':      colis.get('client', '') or '',
                'company':     colis.get('company', '') or '',
                'arc':         colis.get('arc', '') or '',
                'afs':         colis.get('afs', []) or [],
                'hors_prod':   bool(colis.get('hors_prod', False)),
                'hp_desc':     colis.get('hp_desc', '') or '',
                'date_entree': date_entree,
            })

    return palettes


def calculate_stats(palettes):
    today      = datetime.now()
    week_start = today - timedelta(days=today.weekday())

    stats = {
        'par_zone': {
            'hors_production': 0,
            '0_15':   0,
            '15_21':  0,
            '21_28':  0,
            'plus_28': 0,
        },
        'arrivees_semaine': 0,
        'total': len(palettes),
        'details_urgentes': [],
        'details_zone': {
            'hors_production': [],
            '0_15':   [],
            '15_21':  [],
            '21_28':  [],
            'plus_28': [],
        }
    }

    for palette in palettes:
        # Hors production -> pas de delai
        if palette['hors_prod']:
            stats['par_zone']['hors_production'] += 1
            stats['details_zone']['hors_production'].append(palette)
            continue

        date_entree = palette['date_entree']
        if not date_entree:
            stats['par_zone']['hors_production'] += 1
            stats['details_zone']['hors_production'].append(palette)
            continue

        jours = (today - date_entree).days

        if date_entree >= week_start:
            stats['arrivees_semaine'] += 1

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

    return stats


def get_emplacements(palettes_list, n=4):
    """Retourne les n premiers emplacements valides."""
    result = []
    for item in palettes_list:
        palette = item[0] if isinstance(item, tuple) else item
        emp = palette.get('emplacement', '')
        if emp and emp not in ('N/A', ''):
            result.append(emp)
    return ' | '.join(result[:n]) if result else '-'


def generate_pdf(stats, filename='rapport_rack_attente_delais_hebdo.pdf'):
    doc = SimpleDocTemplate(
        filename, pagesize=A4,
        topMargin=1*cm, bottomMargin=1*cm,
        leftMargin=1*cm, rightMargin=1*cm
    )
    story  = []
    styles = getSampleStyleSheet()

    style_bold_r = ParagraphStyle('sbr', parent=styles['Normal'],
                                  fontSize=12, fontName='Helvetica-Bold', alignment=TA_RIGHT)
    style_heading = ParagraphStyle('sh', parent=styles['Normal'],
                                   fontSize=12, fontName='Helvetica-Bold')
    style_red_heading = ParagraphStyle('srh', parent=styles['Normal'],
                                       fontSize=12, fontName='Helvetica-Bold',
                                       textColor=colors.HexColor('#dc2626'))

    # ── TITRE ──
    title_style = ParagraphStyle('title', parent=styles['Normal'],
                                 fontSize=28, fontName='Helvetica-Bold',
                                 textColor=colors.white, alignment=TA_CENTER)
    title_table = Table([[Paragraph("RAPPORT RACK ATTENTE DELAIS AUEM", title_style)]], colWidths=[18*cm])
    title_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), colors.HexColor('#1c1814')),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(title_table)
    story.append(Spacer(1, 0.2*cm))

    week_num = datetime.now().isocalendar()[1]
    story.append(Paragraph(
        f"Semaine {week_num}  -  {datetime.now().year}   |   {datetime.now().strftime('%d/%m/%Y')}",
        ParagraphStyle('date', parent=styles['Normal'], fontSize=11,
                       alignment=TA_CENTER, textColor=colors.HexColor('#666'))
    ))
    story.append(Spacer(1, 0.4*cm))

    # ── MOUVEMENTS ──
    story.append(Paragraph("MOUVEMENTS CETTE SEMAINE", style_heading))
    story.append(Spacer(1, 0.2*cm))

    movements_data = [
        ['Palettes arrivees cette semaine', Paragraph(str(stats['arrivees_semaine']), style_bold_r)],
        ['Total palettes en attente',       Paragraph(str(stats['total']),            style_bold_r)],
        ['Palettes urgentes (+28j)',         Paragraph(str(stats['par_zone']['plus_28']), style_bold_r)],
    ]
    movements_table = Table(movements_data, colWidths=[10*cm, 6*cm])
    movements_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('ALIGN',         (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME',      (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID',          (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
        ('ROWBACKGROUNDS',(0, 0), (-1, -1), [
            colors.white,
            colors.HexColor('#fafafa'),
            colors.HexColor('#fff3cd'),
        ]),
    ]))
    story.append(movements_table)
    story.append(Spacer(1, 0.5*cm))

    # ── REPARTITION ──
    story.append(Paragraph("REPARTITION DES PALETTES", style_heading))
    story.append(Spacer(1, 0.2*cm))

    total = stats['total']
    def pct(n):
        return f"{round(100*n/total, 1) if total > 0 else 0}%"

    zone_data = [
        ['Type de palette', 'Qte', '%', 'Emplacements (exemples)'],
        ['Hors production / sans date',
         str(stats['par_zone']['hors_production']),
         pct(stats['par_zone']['hors_production']),
         get_emplacements(stats['details_zone']['hors_production'])],
        ['0 - 15 jours',
         str(stats['par_zone']['0_15']),
         pct(stats['par_zone']['0_15']),
         get_emplacements(stats['details_zone']['0_15'])],
        ['15 - 21 jours',
         str(stats['par_zone']['15_21']),
         pct(stats['par_zone']['15_21']),
         get_emplacements(stats['details_zone']['15_21'])],
        ['21 - 28 jours',
         str(stats['par_zone']['21_28']),
         pct(stats['par_zone']['21_28']),
         get_emplacements(stats['details_zone']['21_28'])],
        ['+28 jours (URGENT)',
         str(stats['par_zone']['plus_28']),
         pct(stats['par_zone']['plus_28']),
         get_emplacements(stats['details_zone']['plus_28']) +
         ('  DELAI DEPASSE' if stats['details_zone']['plus_28'] else '')],
    ]

    zone_table = Table(zone_data, colWidths=[5.5*cm, 1.5*cm, 1.5*cm, 8.5*cm])
    zone_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), colors.HexColor('#1c1814')),
        ('TEXTCOLOR',     (0, 0), (-1, 0), colors.white),
        ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0), 10),
        ('ALIGN',         (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN',         (0, 1), (2, -1), 'CENTER'),
        ('ALIGN',         (3, 1), (3, -1), 'LEFT'),
        ('FONTSIZE',      (1, 1), (1, -1), 12),
        ('FONTNAME',      (1, 1), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',      (3, 1), (3, -1), 8),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID',          (0, 0), (-1, -1), 1.5, colors.HexColor('#e0e0e0')),
        ('ROWBACKGROUNDS',(0, 1), (-1, -2), [colors.white, colors.HexColor('#f9f9f9')]),
        # Ligne +28j (index 5)
        ('BACKGROUND',    (0, 5), (-1, 5), colors.HexColor('#fee2e2')),
        ('TEXTCOLOR',     (0, 5), (-1, 5), colors.HexColor('#dc2626')),
        ('FONTNAME',      (0, 5), (-1, 5), 'Helvetica-Bold'),
    ]))
    story.append(zone_table)
    story.append(Spacer(1, 0.5*cm))

    # ── PAGE 2 : DETAIL URGENTS ──
    if stats['details_urgentes']:
        story.append(PageBreak())
        story.append(Paragraph("PALETTES URGENTES A TRAITER (+28 jours)", style_red_heading))
        story.append(Spacer(1, 0.3*cm))

        details_tries = sorted(stats['details_urgentes'], key=lambda x: x[1], reverse=True)

        urgent_data = [['Emplacement', 'Client', 'Entreprise', 'Jours', 'Depassement', 'AFS']]
        for palette, jours in details_tries:
            emp     = palette.get('emplacement', '-')
            client  = palette.get('client', '') or (palette.get('hp_desc', '') if palette.get('hors_prod') else '-')
            company = palette.get('company', '') or '-'
            afs     = ', '.join(palette.get('afs', [])) or '-'
            depass  = f"+{jours - 28}j"
            urgent_data.append([emp, client[:20], company[:20], str(jours), depass, afs[:25]])

        urgent_table = Table(urgent_data, colWidths=[2.5*cm, 3.5*cm, 3.5*cm, 1.5*cm, 2*cm, 4*cm])
        urgent_table.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0), colors.HexColor('#dc2626')),
            ('TEXTCOLOR',     (0, 0), (-1, 0), colors.white),
            ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, 0), 9),
            ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN',         (1, 1), (2, -1), 'LEFT'),
            ('FONTSIZE',      (0, 1), (-1, -1), 9),
            ('FONTNAME',      (0, 1), (0, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR',     (0, 1), (0, -1), colors.HexColor('#dc2626')),
            ('TOPPADDING',    (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('GRID',          (0, 0), (-1, -1), 1, colors.HexColor('#fca5a5')),
            ('ROWBACKGROUNDS',(0, 1), (-1, -1), [
                colors.HexColor('#fee2e2'),
                colors.HexColor('#fecaca'),
            ]),
        ]))
        story.append(urgent_table)
    else:
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(
            "Aucune palette urgente - tout est sous controle.",
            ParagraphStyle('ok', parent=styles['Normal'], fontSize=12,
                           textColor=colors.HexColor('#16a34a'), fontName='Helvetica-Bold')
        ))

    # ── PAGE 3 : LISTE COMPLETE ──
    if stats['total'] > 0:
        story.append(PageBreak())
        story.append(Paragraph("LISTE COMPLETE DES PALETTES EN ATTENTE", style_heading))
        story.append(Spacer(1, 0.3*cm))

        all_palettes = []
        for zone_key in ['plus_28', '21_28', '15_21', '0_15', 'hors_production']:
            for item in stats['details_zone'][zone_key]:
                palette = item[0] if isinstance(item, tuple) else item
                jours   = item[1] if isinstance(item, tuple) else None
                all_palettes.append((palette, jours))

        full_header = [['Emplacement', 'Client', 'Entreprise', 'ARC', 'Jours', 'Statut']]
        full_rows   = []
        row_colors  = []

        for i, (palette, jours) in enumerate(all_palettes, start=1):
            emp     = palette.get('emplacement', '-')
            client  = palette.get('client', '') or (palette.get('hp_desc', '') if palette.get('hors_prod') else '-')
            company = palette.get('company', '') or '-'
            arc     = palette.get('arc', '') or '-'

            if palette.get('hors_prod'):
                jours_txt = '-'
                statut    = 'Hors prod.'
                row_colors.append(('BACKGROUND', (0,i), (-1,i), colors.HexColor('#f3e8ff')))
            elif jours is not None:
                jours_txt = str(jours)
                if jours > 28:
                    statut = 'URGENT'
                    row_colors.append(('BACKGROUND', (0,i), (-1,i), colors.HexColor('#fee2e2')))
                    row_colors.append(('TEXTCOLOR',  (5,i), (5,i),  colors.HexColor('#dc2626')))
                    row_colors.append(('FONTNAME',   (5,i), (5,i),  'Helvetica-Bold'))
                elif jours > 21:
                    statut = 'Attention'
                    row_colors.append(('BACKGROUND', (0,i), (-1,i), colors.HexColor('#fefce8')))
                elif jours > 15:
                    statut = 'Surveiller'
                    row_colors.append(('BACKGROUND', (0,i), (-1,i), colors.HexColor('#eff6ff')))
                else:
                    statut = 'OK'
            else:
                jours_txt = '-'
                statut    = '-'

            full_rows.append([emp, client[:22], company[:22], arc[:10], jours_txt, statut])

        full_data  = full_header + full_rows
        full_table = Table(full_data, colWidths=[2.5*cm, 4*cm, 4*cm, 2*cm, 1.5*cm, 3*cm])
        full_table.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0), colors.HexColor('#1c1814')),
            ('TEXTCOLOR',     (0, 0), (-1, 0), colors.white),
            ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, 0), 9),
            ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN',         (1, 1), (2, -1), 'LEFT'),
            ('FONTSIZE',      (0, 1), (-1, -1), 8),
            ('FONTNAME',      (0, 1), (0, -1), 'Helvetica-Bold'),
            ('TOPPADDING',    (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('GRID',          (0, 0), (-1, -1), 0.8, colors.HexColor('#e0e0e0')),
        ] + row_colors))
        story.append(full_table)

    # ── FOOTER ──
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(
        f"Genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')}  -  AUEM Rack Attente Delais",
        ParagraphStyle('footer', parent=styles['Normal'], fontSize=8,
                       alignment=TA_CENTER, textColor=colors.HexColor('#999'))
    ))

    doc.build(story)
    print(f"PDF genere : {filename}")
    return filename


def send_email(pdf_filename, recipient_email):
    try:
        print(f"Envoi a {recipient_email}...")
        msg = MIMEMultipart('mixed')
        msg['Subject'] = f"Rapport Rack AUEM - Semaine {datetime.now().isocalendar()[1]} / {datetime.now().year}"
        msg['From']    = SMTP_USER
        msg['To']      = recipient_email
        msg['Date']    = formatdate(localtime=True)

        html_body = f"""
        <html><body style="font-family:Arial,sans-serif;color:#1c1814;background:#f9f9f9;padding:20px;">
          <div style="max-width:500px;margin:0 auto;background:#fff;border-radius:8px;padding:24px;border:1px solid #e0e0e0;">
            <h2 style="margin:0 0 4px;">Rapport Rack AUEM</h2>
            <p style="color:#888;margin:0 0 16px;font-size:13px;">
              Semaine {datetime.now().isocalendar()[1]} - {datetime.now().year}
            </p>
            <p>Le rapport PDF complet est joint a cet e-mail.</p>
            <p>Il contient :</p>
            <ul>
              <li>Les mouvements de la semaine</li>
              <li>La repartition par zone de delai</li>
              <li>Le detail des palettes urgentes (+28 jours)</li>
              <li>La liste complete des palettes en attente</li>
            </ul>
            <p style="color:#dc2626;font-weight:bold;margin-top:16px;">
              Les palettes avec delai depasse sont marquees en ROUGE.
            </p>
            <hr style="border:none;border-top:1px solid #e0e0e0;margin:20px 0;">
            <p style="font-size:11px;color:#aaa;">
              Genere automatiquement le {datetime.now().strftime('%d/%m/%Y a %H:%M')}
            </p>
          </div>
        </body></html>
        """
        msg.attach(MIMEText(html_body, 'html'))

        with open(pdf_filename, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{pdf_filename}"')
            msg.attach(part)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Email envoye !")
        return True

    except Exception as e:
        print(f"Erreur email : {e}")
        return False


def main():
    print("Generation du rapport rack AUEM")

    print("Recuperation des donnees Firebase...")
    data = fetch_firebase_data()

    print("Parsing des palettes...")
    palettes = parse_palettes(data)
    print(f"  -> {len(palettes)} colis actifs trouves")

    if palettes:
        emps = sorted({p['emplacement'] for p in palettes})
        print(f"  -> Emplacements occupes : {emps}")

    print("Calcul des statistiques...")
    stats = calculate_stats(palettes)
    print(f"  -> Hors prod  : {stats['par_zone']['hors_production']}")
    print(f"  -> 0-15j      : {stats['par_zone']['0_15']}")
    print(f"  -> 15-21j     : {stats['par_zone']['15_21']}")
    print(f"  -> 21-28j     : {stats['par_zone']['21_28']}")
    print(f"  -> +28j URGENT: {stats['par_zone']['plus_28']}")

    print("Generation du PDF...")
    pdf_file = 'rapport_rack_hebdo.pdf'
    generate_pdf(stats, pdf_file)

    print("Envoi de l email...")
    send_email(pdf_file, RAPPORT_EMAIL)

    print("Termine !")


if __name__ == '__main__':
    main()
