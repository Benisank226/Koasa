from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from io import BytesIO
from datetime import datetime
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib.parse
import os

# Configuration email CORRIGÉE
EMAIL_CONFIG = {
    'host': os.environ.get('SMTP_SERVER', 'smtp.gmail.com'),
    'port': int(os.environ.get('SMTP_PORT', 587)),
    'username': os.environ.get('SMTP_USERNAME', 'sankarabienvenu226@gmail.com'),
    'password': os.environ.get('SMTP_PASSWORD', ''),
    'from_name': 'KOASA'
}

def send_email(to_email, subject, html_content):
    """
    Envoie un email réel via SMTP Gmail
    """
    print(f"🔄 TENTATIVE ENVOI EMAIL À: {to_email}")
    try:
        print(f"🔧 CONFIG SMTP: {EMAIL_CONFIG['username']}")
        print(f"🔧 MOT DE PASSE PRÉSENT: {bool(EMAIL_CONFIG['password'])}")
        # Créer le message
        msg = MIMEMultipart()
        msg['From'] = f"{EMAIL_CONFIG['from_name']} <{EMAIL_CONFIG['username']}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Ajouter le contenu HTML
        msg.attach(MIMEText(html_content, 'html'))
        
        # Connexion au serveur SMTP
        server = smtplib.SMTP(EMAIL_CONFIG['host'], EMAIL_CONFIG['port'])
        server.ehlo()  # Identification au serveur
        server.starttls()  # Chiffrement TLS
        server.ehlo()  # Ré-identification après TLS
        
        # Login avec vos identifiants
        server.login(EMAIL_CONFIG['username'], EMAIL_CONFIG['password'])
        
        # Envoi de l'email
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email envoyé avec succès à: {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur envoi email: {e}")
        print(f"📧 Détails - From: {EMAIL_CONFIG['username']}, To: {to_email}")
        return False

def send_verification_email(user, verification_code):
    """Envoie l'email de vérification"""
    subject = "🔐 KOASA - Vérification de votre email"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #dc2626; color: white; padding: 20px; text-align: center; }}
            .content {{ background: #f9f9f9; padding: 20px; }}
            .code {{ font-size: 32px; font-weight: bold; text-align: center; color: #dc2626; margin: 20px 0; padding: 15px; background: #f8f9fa; border: 2px dashed #dc2626; border-radius: 8px; }}
            .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
            .info {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🥩 KOASA Boucherie</h1>
                <h2>Vérification de votre email</h2>
            </div>
            <div class="content">
                <p>Bonjour <strong>{user.first_name}</strong>,</p>
                <p>Merci de vous être inscrit sur KOASA. Pour activer votre compte, veuillez utiliser le code de vérification suivant :</p>
                
                <div class="code">{verification_code}</div>
                
                <div class="info">
                    <p><strong>⏱️ Ce code expire dans 5 minutes</strong></p>
                    <p><strong>📍 Important :</strong> Ce code est nécessaire pour vérifier votre email et continuer le processus d'inscription.</p>
                </div>
                
                <p>Si vous n'avez pas créé de compte sur KOASA, veuillez ignorer cet email.</p>
            </div>
            <div class="footer">
                <p>KOASA Boucherie Sankara & Fils - Ouagadougou, Burkina Faso</p>
                <p>📞 +226 69 62 84 77 | 📧 contact@koasa.bf</p>
                <p>© 2024 KOASA. Tous droits réservés.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(user.email, subject, html_content)

def send_password_reset_email(user, reset_token):
    """Envoie l'email de réinitialisation de mot de passe"""
    subject = "🔐 KOASA - Réinitialisation de votre mot de passe"
    
    reset_url = f"https://koasa.onrender.com/reset-password/{reset_token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #dc2626; color: white; padding: 20px; text-align: center; }}
            .content {{ background: #f9f9f9; padding: 20px; }}
            .button {{ display: inline-block; padding: 12px 24px; background: #dc2626; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; }}
            .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
            .info {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #ffc107; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🥩 KOASA Boucherie</h1>
                <h2>Réinitialisation de mot de passe</h2>
            </div>
            <div class="content">
                <p>Bonjour <strong>{user.first_name}</strong>,</p>
                <p>Vous avez demandé la réinitialisation de votre mot de passe. Cliquez sur le bouton ci-dessous pour créer un nouveau mot de passe :</p>
                
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" class="button">Réinitialiser mon mot de passe</a>
                </p>
                
                <div class="info">
                    <p><strong>⏱️ Ce lien expire dans 1 heure</strong></p>
                    <p>Si le bouton ne fonctionne pas, copiez et collez ce lien dans votre navigateur :</p>
                    <p style="word-break: break-all; background: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace;">
                        {reset_url}
                    </p>
                </div>
                
                <p>Si vous n'avez pas demandé cette réinitialisation, veuillez ignorer cet email.</p>
            </div>
            <div class="footer">
                <p>KOASA Boucherie Sankara & Fils - Ouagadougou, Burkina Faso</p>
                <p>📞 +226 69 62 84 77 | 📧 contact@koasa.bf</p>
                <p>© 2024 KOASA. Tous droits réservés.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(user.email, subject, html_content)

# Fonctions WhatsApp réelles
def generate_whatsapp_link(phone, token, user_name):
    """
    Génère un lien WhatsApp avec message pré-rempli pour l'utilisateur
    L'utilisateur envoie le token à l'admin
    """
    admin_phone = "+22669628477"
    message = f"""
🔐 KOASA - Activation WhatsApp

Bonjour Admin KOASA,

Je suis {user_name} et je souhaite vérifier mon WhatsApp.

Mon token d'activation est :
{token}

Mon numéro: {phone}

Merci de vérifier mon WhatsApp!
"""
    
    encoded_message = urllib.parse.quote(message)
    whatsapp_url = f"https://wa.me/{admin_phone}?text={encoded_message}"
    
    return whatsapp_url

def send_activation_whatsapp(user):
    """Génère le lien WhatsApp pour que l'utilisateur envoie le token à l'admin"""
    whatsapp_url = generate_whatsapp_link(user.phone, user.activation_token, f"{user.first_name} {user.last_name}")
    
    print(f"🔗 Lien WhatsApp généré pour: {user.phone}")
    print(f"📝 Token: {user.activation_token}")
    
    return whatsapp_url

def send_otp_whatsapp(user, otp_code):
    """Envoie le code OTP par WhatsApp (vrai envoi)"""
    message = f"""
🔐 KOASA - Code de vérification WhatsApp

Bonjour {user.first_name},

Votre code de vérification:
{otp_code}

⏱️ Valide pendant 10 minutes.

Ne partagez ce code avec personne!
"""
    
    # Générer le lien WhatsApp pour l'envoi
    encoded_message = urllib.parse.quote(message)
    whatsapp_url = f"https://wa.me/{user.phone}?text={encoded_message}"
    
    print(f"📱 Code OTP WhatsApp généré pour: {user.phone}")
    print(f"🔗 Lien WhatsApp: {whatsapp_url}")
    
    return whatsapp_url

def send_order_confirmation_whatsapp(user, order):
    """Envoie la confirmation de commande par WhatsApp"""
    items_text = "\n".join([
        f"• {item.product_name} - {item.quantity} {item.unit_price} FCFA"
        for item in order.items
    ])
    
    message = f"""
✅ KOASA - Commande confirmée!

Bonjour {user.first_name},

Votre commande a été confirmée par l'admin!

📦 ID Commande: {order.whatsapp_order_id}
💰 Montant total: {order.total_amount:,.0f} FCFA

📋 Détails:
{items_text}

📍 Adresse de livraison:
{order.delivery_address or 'À préciser'}

Votre commande est en préparation! 🥩
Merci de votre confiance! 🙏
"""
    
    encoded_message = urllib.parse.quote(message)
    whatsapp_url = f"https://wa.me/{user.phone}?text={encoded_message}"
    
    return whatsapp_url

def send_activation_confirmation_whatsapp(user):
    """Envoie la confirmation d'activation à l'utilisateur"""
    message = f"""
✅ KOASA - WhatsApp Vérifié!

Bonjour {user.first_name},

Votre WhatsApp a été vérifié avec succès par l'administrateur!

Vous pouvez maintenant passer commande sur KOASA.

Merci de votre confiance! 🥩
"""
    
    encoded_message = urllib.parse.quote(message)
    whatsapp_url = f"https://wa.me/{user.phone}?text={encoded_message}"
    
    return whatsapp_url

# --- FONCTION CORRIGÉE POUR GÉNÉRER LE LIEN WHATSAPP ---
def generate_order_whatsapp_link(cart_items, total, user, whatsapp_order_id, delivery_address="", notes=""):
    """
    Génère un lien WhatsApp avec le récapitulatif de commande pour l'admin
    """
    admin_phone = "+22669628477"
    
    # Formater les items correctement
    items_text = "\n".join([
        f"• {item['name']} - {item['quantity']} {item.get('unit', 'unité')} x {item['price']:,.0f} FCFA = {(item['price'] * item['quantity']):,.0f} FCFA"
        for item in cart_items
    ])
    
    message = f"""
🛒 NOUVELLE COMMANDE KOASA

📋 ID COMMANDE: {whatsapp_order_id}

👤 CLIENT:
Nom: {user.first_name} {user.last_name}
Téléphone: {user.phone}
Email: {user.email}

📦 DÉTAILS DE LA COMMANDE:
{items_text}

💰 TOTAL: {total:,.0f} FCFA

📍 ADRESSE DE LIVRAISON:
{delivery_address or 'À confirmer avec le client'}

📝 NOTES:
{notes or 'Aucune note'}

⏰ Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Merci de préparer cette commande! 🥩
"""
    
    # Encodage URL correct
    encoded_message = urllib.parse.quote(message)
    whatsapp_url = f"https://wa.me/{admin_phone}?text={encoded_message}"
    
    print(f"🔗 Lien WhatsApp généré: {whatsapp_url}")
    return whatsapp_url

def generate_invoice_pdf(order, user):
    """Génère une facture PDF pour une commande"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#dc2626'),
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#dc2626'),
        spaceAfter=12
    )
    
    # En-tête
    elements.append(Paragraph("🥩 KOASA", title_style))
    elements.append(Paragraph("Boucherie Sankara & Fils", styles['Normal']))
    elements.append(Paragraph("Ouagadougou, Burkina Faso", styles['Normal']))
    elements.append(Paragraph("Tél: +226 XX XX XX XX", styles['Normal']))
    elements.append(Spacer(1, 1*cm))
    
    # Titre facture
    elements.append(Paragraph(f"FACTURE N° {order.whatsapp_order_id}", header_style))
    elements.append(Paragraph(f"Date: {order.created_at.strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))
    
    # Informations client
    elements.append(Paragraph("INFORMATIONS CLIENT", header_style))
    client_info = f"""
    <b>Nom:</b> {user.first_name} {user.last_name}<br/>
    <b>Email:</b> {user.email}<br/>
    <b>Téléphone:</b> {user.phone}
    """
    elements.append(Paragraph(client_info, styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))
    
    # Statut de la commande
    status_text = "EN ATTENTE"
    if order.status == 'confirme':
        status_text = "CONFIRMÉE"
    elif order.status == 'preparation':
        status_text = "EN PRÉPARATION"
    elif order.status == 'livree':
        status_text = "LIVRÉE"
    
    elements.append(Paragraph(f"STATUT: {status_text}", header_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Tableau des articles
    elements.append(Paragraph("DÉTAILS DE LA COMMANDE", header_style))
    
    data = [['Article', 'Quantité', 'Prix Unitaire', 'Sous-total']]
    
    for item in order.items:
        data.append([
            item.product_name,
            f"{item.quantity}",
            f"{item.unit_price:,.0f} FCFA",
            f"{item.subtotal:,.0f} FCFA"
        ])
    
    data.append(['', '', 'TOTAL', f"{order.total_amount:,.0f} FCFA"])
    
    table = Table(data, colWidths=[8*cm, 3*cm, 4*cm, 4*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc2626')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fee2e2')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#fef2f2')])
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 1*cm))
    
    # Adresse de livraison
    if order.delivery_address:
        elements.append(Paragraph("ADRESSE DE LIVRAISON", header_style))
        elements.append(Paragraph(order.delivery_address, styles['Normal']))
        elements.append(Spacer(1, 0.5*cm))
    
    # Notes
    if order.notes:
        elements.append(Paragraph("NOTES", header_style))
        elements.append(Paragraph(order.notes, styles['Normal']))
        elements.append(Spacer(1, 0.5*cm))
    
    # Pied de page
    elements.append(Paragraph("Merci de votre confiance! 🙏", styles['Italic']))
    elements.append(Paragraph("KOASA - Votre boucherie de qualité", styles['Italic']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

def format_whatsapp_cart_message(cart_items, total, user):
    """Formate le message WhatsApp pour le panier"""
    items_text = "\n".join([
        f"• {item['name']} - {item['quantity']} x {item['price']:,.0f} = {item['subtotal']:,.0f} FCFA"
        for item in cart_items
    ])
    
    message = f"""
🛒 KOASA - Récapitulatif de votre panier

Bonjour {user.first_name},

Voici votre commande:

{items_text}

💰 Total: {total:,.0f} FCFA

Pour confirmer votre commande, rendez-vous sur notre site.

Merci! 🥩
"""
    return message