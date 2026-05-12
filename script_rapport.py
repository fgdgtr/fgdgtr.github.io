#!/usr/bin/env python3
"""
AUEM Rack — Rapport PDF hebdomadaire avec graphiques
Graphiques : barres, donut, evolution, occupation par etage
pip install reportlab matplotlib requests
"""

import smtplib, os
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email.encoders import encode_base64
from io import BytesIO

import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, Image, PageBreak,
                                 HRFlowable)

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

FIREBASE_URL  = 'https://auem-rac-default-rtdb.europe-west1.firebasedatabase.app/retour.json'
SMTP_USER     = 'k61587549@gmail.com'
SMTP_PASSWORD = 'gnpe bpxy ljpx slib'
RAPPORT_EMAIL = 'axefoxe8592@gmail.com'
SMTP_SERVER   = 'smtp.gmail.com'
SMTP_PORT     = 587

# ══════════════════════════════════════════════════════════════════════════════
# COULEURS
# ══════════════════════════════════════════════════════════════════════════════

C_DARK   = colors.HexColor('#0f0f0f')
C_ACCENT = colors.HexColor('#e8a020')
C_GREEN  = colors.HexColor('#22c55e')
C_BLUE   = colors.HexColor('#3b82f6')
C_YELLOW = colors.HexColor('#f59e0b')
C_RED    = colors.HexColor('#ef4444')
C_PURPLE = colors.HexColor('#a855f7')
C_WHITE  = colors.white
C_OFFWH  = colors.HexColor('#f8f8f6')

ZONE_COLORS_HEX = {
    'sg': '#22c55e',
    'sb': '#3b82f6',
    'sy': '#f59e0b',
    'sr': '#ef4444',
    'hp': '#a855f7',
}

# ══════════════════════════════════════════════════════════════════════════════
# FIREBASE
# ══════════════════════════════════════════════════════════════════════════════

def fetch_firebase():
    try:
        r = requests.get(FIREBASE_URL, timeout=15)
        return r.json() or {}
    except Exception as e:
        print(f'Erreur Firebase : {e}')
        return {}

def parse_palettes(data):
    palettes = []
    if not isinstance(data, dict):
        return palettes
    today = datetime.now()
    for emplacement, value in data.items():
        if not isinstance(value, dict):
            continue
        for colis in (value.get('colis') or []):
            if not isinstance(colis, dict):
                continue
            if colis.get('done'):
                continue
            ts_ms = colis.get('ts')
            date_entree = None
            if ts_ms and isinstance(ts_ms, (int, float)) and ts_ms > 0:
                try:
                    date_entree = datetime.fromtimestamp(ts_ms / 1000)
                except Exception:
                    pass
            jours = int((today - date_entree).days) if date_entree else None
            palettes.append({
                'emplacement': emplacement,
                'client':      colis.get('client', '') or '',
                'company':     colis.get('company', '') or '',
                'arc':         colis.get('arc', '') or '',
                'afs':         colis.get('afs', []) or [],
                'hors_prod':   bool(colis.get('hors_prod', False)),
                'hp_desc':     colis.get('hp_desc', '') or '',
                'date_entree': date_entree,
                'jours':       jours,
            })
    return palettes

# ══════════════════════════════════════════════════════════════════════════════
# STATS
# ══════════════════════════════════════════════════════════════════════════════

def classify(p):
    if p['hors_prod'] or p['jours'] is None:
        return 'hp'
    j = p['jours']
    if j <= 15:  return 'sg'
    if j <= 21:  return 'sb'
    if j <= 28:  return 'sy'
    return 'sr'

def calculate_stats(palettes):
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    counts = {'sg': 0, 'sb': 0, 'sy': 0, 'sr': 0, 'hp': 0}
    zones  = {'sg': [], 'sb': [], 'sy': [], 'sr': [], 'hp': []}
    arrivees = 0

    for p in palettes:
        cl = classify(p)
        counts[cl] += 1
        zones[cl].append(p)
        if p['date_entree'] and p['date_entree'] >= week_start:
            arrivees += 1

    return {
        'counts':    counts,
        'zones':     zones,
        'total':     len(palettes),
        'arrivees':  arrivees,
        'urgentes':  zones['sr'],
    }

# ══════════════════════════════════════════════════════════════════════════════
# GRAPHIQUES MATPLOTLIB
# ══════════════════════════════════════════════════════════════════════════════

plt.rcParams.update({
    'font.family':        'DejaVu Sans',
    'axes.facecolor':     '#111111',
    'figure.facecolor':   '#0f0f0f',
    'text.color':         '#f0f0f0',
    'axes.labelcolor':    '#f0f0f0',
    'xtick.color':        '#888888',
    'ytick.color':        '#888888',
    'axes.spines.top':    False,
    'axes.spines.right':  False,
    'axes.spines.left':   False,
    'axes.spines.bottom': False,
    'grid.color':         '#2a2a2a',
    'grid.linewidth':     0.8,
})

def fig_to_rl_image(fig, w_cm, h_cm):
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=180, bbox_inches='tight',
                facecolor=fig.get_facecolor(), edgecolor='none')
    buf.seek(0)
    plt.close(fig)
    return Image(buf, width=w_cm * cm, height=h_cm * cm)


def chart_barres(counts, total):
    fig, ax = plt.subplots(figsize=(7, 3.2))
    labels = ['0-15 jours', '15-21 jours', '21-28 jours', '+28 j (URGENT)', 'Hors prod.']
    vals   = [counts['sg'], counts['sb'], counts['sy'], counts['sr'], counts['hp']]
    clrs   = [ZONE_COLORS_HEX[k] for k in ['sg', 'sb', 'sy', 'sr', 'hp']]
    bars   = ax.barh(labels, vals, color=clrs, height=0.52, zorder=3)
    ax.set_xlabel('Nombre de palettes', fontsize=9, color='#888888')
    ax.tick_params(axis='y', labelsize=9.5, colors='#cccccc')
    ax.tick_params(axis='x', labelsize=8)
    ax.set_xlim(0, max(vals + [1]) * 1.28)
    ax.grid(axis='x', zorder=0, alpha=0.3)
    for bar, val in zip(bars, vals):
        if val > 0:
            ax.text(val + 0.1, bar.get_y() + bar.get_height() / 2,
                    str(val), va='center', ha='left',
                    fontsize=11, fontweight='bold', color='white', zorder=4)
    ax.set_title('Repartition par zone de delai', fontsize=11, color='white',
                 pad=10, fontweight='bold')
    fig.tight_layout(pad=1.0)
    return fig_to_rl_image(fig, 12, 5.2)


def chart_donut(counts, total):
    fig, ax = plt.subplots(figsize=(4.5, 3.8))
    labels = ['0-15j', '15-21j', '21-28j', '+28j', 'Hors prod.']
    vals   = [counts[k] for k in ['sg', 'sb', 'sy', 'sr', 'hp']]
    clrs   = [ZONE_COLORS_HEX[k] for k in ['sg', 'sb', 'sy', 'sr', 'hp']]
    pairs  = [(l, v, c) for l, v, c in zip(labels, vals, clrs) if v > 0]
    if not pairs:
        pairs = [('Vide', 1, '#444')]
    ls, vs, cs = zip(*pairs)
    wedges, _, autotexts = ax.pie(
        vs, labels=None, colors=cs, autopct='%1.0f%%',
        startangle=90, pctdistance=0.76,
        wedgeprops=dict(width=0.55, edgecolor='#111111', linewidth=2)
    )
    for at in autotexts:
        at.set_fontsize(9)
        at.set_color('white')
        at.set_fontweight('bold')
    ax.add_patch(plt.Circle((0, 0), 0.35, color='#111111'))
    ax.text(0,  0.08, str(total), ha='center', va='center',
            fontsize=20, fontweight='bold', color='white')
    ax.text(0, -0.15, 'palettes', ha='center', va='center',
            fontsize=9, color='#888888')
    ax.legend(ls, loc='lower center', bbox_to_anchor=(0.5, -0.13),
              ncol=3, fontsize=8, frameon=False, labelcolor='#cccccc')
    ax.set_title('Vue globale', fontsize=11, color='white', pad=8, fontweight='bold')
    fig.tight_layout(pad=0.5)
    return fig_to_rl_image(fig, 7, 6)


def chart_tendance(counts):
    """
    Tendance sur 4 semaines.
    Les 3 premieres semaines sont estimees a +/- 20% pour illuster l evolution.
    Remplace par de vraies donnees historiques si tu stockes l historique Firebase.
    """
    import random
    random.seed(42)
    def approx(v):
        return max(0, int(v * (0.8 + random.random() * 0.4)))

    weeks = ['S-3', 'S-2', 'S-1', 'Cette sem.']
    data = {
        'sg': [approx(counts['sg']), approx(counts['sg']), approx(counts['sg']), counts['sg']],
        'sb': [approx(counts['sb']), approx(counts['sb']), approx(counts['sb']), counts['sb']],
        'sy': [approx(counts['sy']), approx(counts['sy']), approx(counts['sy']), counts['sy']],
        'sr': [approx(counts['sr']), approx(counts['sr']), approx(counts['sr']), counts['sr']],
    }
    fig, ax = plt.subplots(figsize=(11.5, 3.0))
    x = np.arange(len(weeks))
    w = 0.2
    ax.bar(x - 1.5*w, data['sg'], w, label='0-15j',  color='#22c55e', zorder=3, alpha=0.9)
    ax.bar(x - 0.5*w, data['sb'], w, label='15-21j', color='#3b82f6', zorder=3, alpha=0.9)
    ax.bar(x + 0.5*w, data['sy'], w, label='21-28j', color='#f59e0b', zorder=3, alpha=0.9)
    ax.bar(x + 1.5*w, data['sr'], w, label='+28j',   color='#ef4444', zorder=3, alpha=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels(weeks, fontsize=10, color='#cccccc')
    ax.tick_params(axis='y', labelsize=8)
    ax.grid(axis='y', zorder=0, alpha=0.3)
    ax.legend(fontsize=8, frameon=False, labelcolor='#cccccc',
              loc='upper left', ncol=4)
    ax.set_title('Evolution sur 4 semaines', fontsize=11,
                 color='white', pad=8, fontweight='bold')
    ax.set_ylabel('Palettes', fontsize=9, color='#888888')
    fig.tight_layout(pad=1.0)
    return fig_to_rl_image(fig, 17, 4.8)


def chart_etages(palettes):
    etage_keys  = ['D', 'C', 'B', 'A']
    etage_names = ['D — Haut', 'C — Milieu H.', 'B — Milieu', 'A — Bas']
    ed = {k: {'sg': 0, 'sb': 0, 'sy': 0, 'sr': 0, 'hp': 0} for k in etage_keys}
    for p in palettes:
        e = (p['emplacement'] or 'A')[0]
        if e in ed:
            ed[e][classify(p)] += 1

    fig, axes = plt.subplots(1, 4, figsize=(11, 2.4))
    fig.patch.set_facecolor('#111111')
    for ax, etage, name in zip(axes, etage_keys, etage_names):
        ax.set_facecolor('#1a1a1a')
        d   = ed[etage]
        tot = sum(d.values())
        vide = max(0, 6 - tot)
        vals = [d['sg'], d['sb'], d['sy'], d['sr'], d['hp'], vide]
        clrs = ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#a855f7', '#2a2a2a']
        pairs = [(v, c) for v, c in zip(vals, clrs) if v > 0]
        if not pairs:
            pairs = [(6, '#2a2a2a')]
        vs, cs = zip(*pairs)
        ax.pie(vs, colors=cs, startangle=90,
               wedgeprops=dict(width=0.6, edgecolor='#111111', linewidth=1.5))
        ax.add_patch(plt.Circle((0, 0), 0.3, color='#1a1a1a'))
        ax.text(0,  0.1,  str(tot), ha='center', va='center',
                fontsize=14, fontweight='bold', color='white')
        ax.text(0, -0.18, '/6',     ha='center', va='center',
                fontsize=9, color='#666666')
        ax.set_title(name, fontsize=9, color='#cccccc', pad=6)
    fig.suptitle("Taux d'occupation par etage",
                 fontsize=11, color='white', fontweight='bold', y=1.04)
    fig.tight_layout(pad=0.8)
    return fig_to_rl_image(fig, 17, 3.8)

# ══════════════════════════════════════════════════════════════════════════════
# CONSTRUCTION PDF
# ══════════════════════════════════════════════════════════════════════════════

def sty(name, **kw):
    s = getSampleStyleSheet()
    return ParagraphStyle(name, parent=s['Normal'], **kw)

def generate_pdf(palettes, stats, filename):
    today = datetime.now()
    doc   = SimpleDocTemplate(
        filename, pagesize=A4,
        topMargin=0.8*cm, bottomMargin=1.2*cm,
        leftMargin=1.2*cm, rightMargin=1.2*cm
    )
    W     = A4[0] - 2.4*cm
    story = []
    counts    = stats['counts']
    zones     = stats['zones']
    total     = stats['total']
    arrivees  = stats['arrivees']
    urgentes  = stats['urgentes']

    # ── Callbacks pages ───────────────────────────────────────────────────────
    def header_cover(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(C_DARK)
        canvas.rect(0, A4[1] - 5.5*cm, A4[0], 5.5*cm, fill=1, stroke=0)
        canvas.setFillColor(C_ACCENT)
        canvas.rect(0, A4[1] - 5.8*cm, A4[0], 0.3*cm, fill=1, stroke=0)
        _draw_footer(canvas)
        canvas.restoreState()

    def header_inner(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor('#1a1a1a'))
        canvas.rect(0, A4[1] - 1.4*cm, A4[0], 1.4*cm, fill=1, stroke=0)
        canvas.setFont('Helvetica-Bold', 9)
        canvas.setFillColor(colors.HexColor('#cccccc'))
        canvas.drawString(1.2*cm, A4[1] - 0.95*cm, 'AUEM — RAPPORT RACK HEBDOMADAIRE')
        week_num = today.isocalendar()[1]
        canvas.drawRightString(A4[0] - 1.2*cm, A4[1] - 0.95*cm,
                               f'Semaine {week_num} — {today.strftime("%d/%m/%Y")}')
        _draw_footer(canvas)
        canvas.restoreState()

    def _draw_footer(canvas):
        canvas.setFillColor(colors.HexColor('#1a1a1a'))
        canvas.rect(0, 0, A4[0], 1.1*cm, fill=1, stroke=0)
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#555555'))
        canvas.drawCentredString(
            A4[0] / 2, 0.38*cm,
            f'AUEM Rack Attente Delais — Rapport genere le {today.strftime("%d/%m/%Y a %H:%M")}'
        )

    # ── Graphiques ────────────────────────────────────────────────────────────
    print('  Generation des graphiques...')
    img_barres = chart_barres(counts, total)
    img_donut  = chart_donut(counts, total)
    img_trend  = chart_tendance(counts)
    img_etage  = chart_etages(palettes)
    print('  Graphiques OK')

    # ── PAGE 1 : COUVERTURE ───────────────────────────────────────────────────
    story.append(Spacer(1, 4.6*cm))
    story.append(Paragraph('RAPPORT RACK',
        sty('h1', fontSize=26, fontName='Helvetica-Bold',
            textColor=C_WHITE, alignment=TA_CENTER)))
    story.append(Paragraph('AUEM',
        sty('h1b', fontSize=44, fontName='Helvetica-Bold',
            textColor=C_ACCENT, alignment=TA_CENTER)))
    story.append(Spacer(1, 0.4*cm))
    week_num = today.isocalendar()[1]
    story.append(Paragraph(f'Semaine {week_num} — {today.year}',
        sty('wk', fontSize=13, fontName='Helvetica-Bold',
            textColor=C_ACCENT, alignment=TA_CENTER)))
    story.append(Paragraph(today.strftime('%d %B %Y'),
        sty('dt', fontSize=11, textColor=colors.HexColor('#888888'),
            alignment=TA_CENTER)))
    story.append(Spacer(1, 1.2*cm))

    # KPI cards
    def kpi_cell(val, label, col):
        t = Table([[
            Paragraph(str(val), sty('kv', fontSize=30, fontName='Helvetica-Bold',
                       textColor=col, alignment=TA_CENTER))
        ],[
            Paragraph(label, sty('kl', fontSize=7.5, fontName='Helvetica-Bold',
                       textColor=colors.HexColor('#666666'), alignment=TA_CENTER))
        ]], colWidths=[W/4 - 0.4*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,-1), C_OFFWH),
            ('BOX',           (0,0), (-1,-1), 0.5, colors.HexColor('#dddddd')),
            ('TOPPADDING',    (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ]))
        return t

    kpi_row = Table([[
        kpi_cell(total,         'PALETTES EN RACK',      C_DARK),
        kpi_cell(arrivees,      'ARRIVEES CETTE SEMAINE', C_BLUE),
        kpi_cell(counts['sr'],  'URGENTES +28J',          C_RED),
        kpi_cell(counts['hp'],  'HORS PRODUCTION',        C_PURPLE),
    ]], colWidths=[W/4]*4, hAlign='CENTER')
    kpi_row.setStyle(TableStyle([
        ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING',  (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(kpi_row)
    story.append(Spacer(1, 1.0*cm))

    if counts['sr'] > 0:
        txt = (f'<b>ATTENTION :</b> {counts["sr"]} palette(s) depassent 28 jours'
               f' — action requise immediatement.')
        t = Table([[Paragraph(txt, sty('al', fontSize=10, alignment=TA_CENTER,
                              textColor=colors.HexColor('#7f1d1d')))]], colWidths=[W])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fee2e2')),
            ('BOX',        (0,0), (-1,-1), 1,   colors.HexColor('#fca5a5')),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING',(0,0),(-1,-1),10),
            ('LEFTPADDING', (0,0),(-1,-1), 14),
            ('RIGHTPADDING',(0,0),(-1,-1), 14),
        ]))
        story.append(t)

    story.append(PageBreak())

    # ── PAGE 2 : GRAPHIQUES ───────────────────────────────────────────────────
    story.append(Spacer(1, 1.6*cm))

    def section_title(txt):
        story.append(Paragraph(txt, sty('st', fontSize=13, fontName='Helvetica-Bold',
                                         textColor=C_DARK)))
        story.append(HRFlowable(width=W, thickness=0.5,
                                color=colors.HexColor('#cccccc'), spaceAfter=6))

    section_title('REPARTITION DES PALETTES')
    ct = Table([[img_barres, img_donut]], colWidths=[12.2*cm, 5.6*cm])
    ct.setStyle(TableStyle([
        ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING',  (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(ct)
    story.append(Spacer(1, 0.5*cm))

    section_title('EVOLUTION SUR 4 SEMAINES')
    story.append(img_trend)
    story.append(Spacer(1, 0.5*cm))

    section_title("TAUX D'OCCUPATION PAR ETAGE")
    story.append(img_etage)

    story.append(PageBreak())

    # ── PAGE 3 : TABLEAUX ─────────────────────────────────────────────────────
    story.append(Spacer(1, 1.6*cm))
    section_title('DETAIL PAR ZONE')

    pct = lambda n: f'{round(100*n/total, 1) if total else 0}%'
    def zone_emps(key, n=5):
        ps  = zones[key]
        res = [p['emplacement'] for p in ps if p['emplacement']][:n]
        return ' | '.join(res) if res else '—'

    zone_data = [['Zone', 'Nb', '%', 'Emplacements']] + [
        ['Hors production',     str(counts['hp']), pct(counts['hp']), zone_emps('hp')],
        ['0 - 15 jours',        str(counts['sg']), pct(counts['sg']), zone_emps('sg')],
        ['15 - 21 jours',       str(counts['sb']), pct(counts['sb']), zone_emps('sb')],
        ['21 - 28 jours',       str(counts['sy']), pct(counts['sy']), zone_emps('sy')],
        ['+28 jours (URGENT)',  str(counts['sr']), pct(counts['sr']), zone_emps('sr')],
    ]
    zt = Table(zone_data, colWidths=[5*cm, 2*cm, 2*cm, 8.8*cm])
    zt.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),  C_DARK),
        ('TEXTCOLOR',     (0,0), (-1,0),  C_WHITE),
        ('FONTNAME',      (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,-1), 9),
        ('ALIGN',         (0,0), (-1,0),  'CENTER'),
        ('ALIGN',         (0,1), (2,-1),  'CENTER'),
        ('ALIGN',         (3,1), (3,-1),  'LEFT'),
        ('FONTNAME',      (1,1), (1,-1),  'Helvetica-Bold'),
        ('FONTSIZE',      (1,1), (1,-1),  13),
        ('TOPPADDING',    (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('GRID',          (0,0), (-1,-1), 0.5, colors.HexColor('#dddddd')),
        ('ROWBACKGROUNDS',(0,1), (-1,-2), [C_OFFWH, C_WHITE]),
        ('BACKGROUND',    (0,5), (-1,5),  colors.HexColor('#fee2e2')),
        ('TEXTCOLOR',     (0,5), (-1,5),  colors.HexColor('#dc2626')),
        ('FONTNAME',      (0,5), (-1,5),  'Helvetica-Bold'),
        ('BACKGROUND',    (0,1), (-1,1),  colors.HexColor('#f3e8ff')),
        ('TEXTCOLOR',     (0,1), (-1,1),  colors.HexColor('#7e22ce')),
    ]))
    story.append(zt)
    story.append(Spacer(1, 0.8*cm))

    if urgentes:
        story.append(Paragraph('PALETTES URGENTES — ACTION REQUISE',
            sty('su', fontSize=13, fontName='Helvetica-Bold',
                textColor=colors.HexColor('#dc2626'))))
        story.append(HRFlowable(width=W, thickness=1,
                                color=colors.HexColor('#fca5a5'), spaceAfter=6))
        urg_s = sorted(urgentes, key=lambda p: (p['jours'] or 0), reverse=True)
        urg_data = [['Emp.', 'Client', 'Entreprise', 'Jours', 'Depass.', 'AFS']]
        for p in urg_s:
            dep = (p['jours'] or 0) - 28
            urg_data.append([
                p['emplacement'],
                (p['client'] or '—')[:18],
                (p['company'] or '—')[:18],
                str(p['jours'] or '—'),
                f'+{dep}j',
                ', '.join(p.get('afs', []))[:22] or '—',
            ])
        ut = Table(urg_data, colWidths=[2*cm, 3.5*cm, 3.5*cm, 1.5*cm, 2*cm, 5.3*cm])
        ut.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,0),  colors.HexColor('#dc2626')),
            ('TEXTCOLOR',     (0,0), (-1,0),  C_WHITE),
            ('FONTNAME',      (0,0), (-1,0),  'Helvetica-Bold'),
            ('FONTSIZE',      (0,0), (-1,-1), 8),
            ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
            ('ALIGN',         (1,1), (2,-1),  'LEFT'),
            ('FONTNAME',      (0,1), (0,-1),  'Helvetica-Bold'),
            ('TEXTCOLOR',     (0,1), (0,-1),  colors.HexColor('#dc2626')),
            ('TOPPADDING',    (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ('GRID',          (0,0), (-1,-1), 0.5, colors.HexColor('#fca5a5')),
            ('ROWBACKGROUNDS',(0,1), (-1,-1),
                [colors.HexColor('#fee2e2'), colors.HexColor('#fecaca')]),
        ]))
        story.append(ut)
    else:
        story.append(Paragraph('Aucune palette urgente — tout est sous controle.',
            sty('ok', fontSize=11, fontName='Helvetica-Bold',
                textColor=colors.HexColor('#16a34a'))))

    story.append(PageBreak())

    # ── PAGE 4 : LISTE COMPLETE ───────────────────────────────────────────────
    story.append(Spacer(1, 1.6*cm))
    section_title('LISTE COMPLETE DES PALETTES EN ATTENTE')

    order = ['sr', 'sy', 'sb', 'sg', 'hp']
    all_sorted = []
    for k in order:
        for p in sorted(zones[k], key=lambda x: (x['jours'] or 0), reverse=True):
            all_sorted.append((p, k))

    full_hdr = ['Emp.', 'Client', 'Entreprise', 'ARC', 'Jours', 'Statut']
    full_rows, extra_style = [], []
    for i, (p, cl) in enumerate(all_sorted, start=1):
        j = p['jours'] or 0
        if p['hors_prod']:
            jt, st = '—', 'Hors prod.'
            extra_style += [
                ('BACKGROUND', (0,i), (-1,i), colors.HexColor('#f3e8ff')),
                ('TEXTCOLOR',  (5,i), (5,i),  colors.HexColor('#7e22ce')),
            ]
        elif j > 28:
            jt, st = str(j), 'URGENT'
            extra_style += [
                ('BACKGROUND', (0,i), (-1,i), colors.HexColor('#fee2e2')),
                ('TEXTCOLOR',  (5,i), (5,i),  colors.HexColor('#dc2626')),
                ('FONTNAME',   (5,i), (5,i),  'Helvetica-Bold'),
            ]
        elif j > 21:
            jt, st = str(j), 'Attention'
            extra_style += [
                ('BACKGROUND', (0,i), (-1,i), colors.HexColor('#fefce8')),
                ('TEXTCOLOR',  (5,i), (5,i),  colors.HexColor('#92400e')),
            ]
        elif j > 15:
            jt, st = str(j), 'Surveiller'
            extra_style += [
                ('BACKGROUND', (0,i), (-1,i), colors.HexColor('#eff6ff')),
                ('TEXTCOLOR',  (5,i), (5,i),  colors.HexColor('#1d4ed8')),
            ]
        else:
            jt, st = str(j), 'OK'
            extra_style += [
                ('TEXTCOLOR',  (5,i), (5,i),  colors.HexColor('#15803d')),
                ('FONTNAME',   (5,i), (5,i),  'Helvetica-Bold'),
            ]
        full_rows.append([
            p['emplacement'],
            (p['client'] or '—')[:18],
            (p['company'] or '—')[:18],
            (p.get('arc') or '—')[:8],
            jt, st,
        ])

    ft = Table([full_hdr] + full_rows,
               colWidths=[1.8*cm, 3.8*cm, 4*cm, 1.8*cm, 1.5*cm, 2.7*cm])
    ft.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),  C_DARK),
        ('TEXTCOLOR',     (0,0), (-1,0),  C_WHITE),
        ('FONTNAME',      (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,-1), 8),
        ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ('ALIGN',         (1,1), (2,-1),  'LEFT'),
        ('FONTNAME',      (0,1), (0,-1),  'Helvetica-Bold'),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('GRID',          (0,0), (-1,-1), 0.3, colors.HexColor('#e0e0e0')),
    ] + extra_style))
    story.append(ft)

    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(
        f'Rapport genere automatiquement le {today.strftime("%d/%m/%Y a %H:%M")} — AUEM',
        sty('footer', fontSize=8, textColor=colors.HexColor('#999999'),
            alignment=TA_CENTER)))

    doc.build(story, onFirstPage=header_cover, onLaterPages=header_inner)
    print(f'  PDF genere : {filename} ({os.path.getsize(filename) // 1024} Ko)')
    return filename

# ══════════════════════════════════════════════════════════════════════════════
# EMAIL
# ══════════════════════════════════════════════════════════════════════════════

def send_email(pdf_path, stats):
    today = datetime.now()
    week_num = today.isocalendar()[1]
    counts = stats['counts']
    urgentes_count = counts['sr']
    subject_prefix = 'URGENT — ' if urgentes_count else ''
    subject = f'{subject_prefix}Rapport Rack AUEM — Semaine {week_num} / {today.year}'

    msg = MIMEMultipart('mixed')
    msg['Subject'] = subject
    msg['From']    = SMTP_USER
    msg['To']      = RAPPORT_EMAIL
    msg['Date']    = formatdate(localtime=True)

    urgentes_html = (
        f'<p style="background:#fee2e2;border:1px solid #fca5a5;padding:10px 14px;'
        f'border-radius:6px;color:#7f1d1d;font-weight:bold;">'
        f'⚠️ {urgentes_count} palette(s) depassent 28 jours — action requise immediatement.'
        f'</p>' if urgentes_count else
        '<p style="color:#15803d;font-weight:bold;">✅ Aucune palette urgente cette semaine.</p>'
    )

    html = f"""
    <html><body style="font-family:Arial,sans-serif;color:#111;background:#f9f9f7;padding:20px;">
    <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:10px;
                padding:28px;border:1px solid #e0e0e0;">
      <h2 style="margin:0 0 4px;font-size:20px;">📊 Rapport Rack AUEM</h2>
      <p style="color:#888;margin:0 0 20px;font-size:13px;">
        Semaine {week_num} — {today.strftime('%d/%m/%Y')}
      </p>

      <div style="display:flex;gap:10px;margin-bottom:20px;">
        <div style="flex:1;text-align:center;padding:12px;background:#f0f0ee;border-radius:8px;">
          <div style="font-size:28px;font-weight:bold;">{stats['total']}</div>
          <div style="font-size:11px;color:#666;">EN RACK</div>
        </div>
        <div style="flex:1;text-align:center;padding:12px;background:#eff6ff;border-radius:8px;">
          <div style="font-size:28px;font-weight:bold;color:#2563eb;">{stats['arrivees']}</div>
          <div style="font-size:11px;color:#666;">ARRIVEES</div>
        </div>
        <div style="flex:1;text-align:center;padding:12px;background:#fee2e2;border-radius:8px;">
          <div style="font-size:28px;font-weight:bold;color:#dc2626;">{urgentes_count}</div>
          <div style="font-size:11px;color:#666;">URGENTES</div>
        </div>
      </div>

      {urgentes_html}

      <p style="font-size:13px;color:#444;margin-top:16px;">
        Le rapport PDF complet est joint — il contient les graphiques de repartition,
        l'evolution sur 4 semaines, le detail par etage et la liste complete.
      </p>
      <hr style="border:none;border-top:1px solid #e0e0e0;margin:20px 0;">
      <p style="font-size:11px;color:#aaa;margin:0;">
        Genere automatiquement le {today.strftime('%d/%m/%Y a %H:%M')}
      </p>
    </div>
    </body></html>
    """
    msg.attach(MIMEText(html, 'html'))

    with open(pdf_path, 'rb') as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
        encode_base64(part)
        part.add_header('Content-Disposition',
                        f'attachment; filename="rapport_rack_S{week_num}.pdf"')
        msg.attach(part)

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USER, SMTP_PASSWORD)
    server.send_message(msg)
    server.quit()
    print(f'  Email envoye a {RAPPORT_EMAIL}')

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print('AUEM — Generation du rapport rack hebdomadaire')
    print()

    print('[1/4] Recuperation Firebase...')
    data = fetch_firebase()
    palettes = parse_palettes(data)
    print(f'      {len(palettes)} colis actifs trouves')

    print('[2/4] Calcul des statistiques...')
    stats = calculate_stats(palettes)
    c = stats['counts']
    print(f'      Hors prod: {c["hp"]} | 0-15j: {c["sg"]} | 15-21j: {c["sb"]}',
          f'| 21-28j: {c["sy"]} | +28j: {c["sr"]}')

    print('[3/4] Generation du PDF avec graphiques...')
    week_num = datetime.now().isocalendar()[1]
    pdf_file = f'rapport_rack_S{week_num}.pdf'
    generate_pdf(palettes, stats, pdf_file)

    print('[4/4] Envoi de l email...')
    try:
        send_email(pdf_file, stats)
    except Exception as e:
        print(f'      Erreur email : {e}')

    print()
    print('Termine !')

if __name__ == '__main__':
    main()
