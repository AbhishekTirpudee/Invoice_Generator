from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, Flowable
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch

@dataclass
class Client:
    name: str
    email: str
    address: str
    contact: Optional[int] = None

@dataclass
class Item:
    name: str
    qty: float
    price: float
    charge_types: List[str] = None
    charge_amounts: List[float] = None

    def price_cal(self):
        base = self.qty * self.price
        extras = sum(self.charge_amounts or [])
        return base + extras

class Invoice:
    def __init__(self, client):
        self.client = client
        self.items = []
        self.invoice_date = datetime.now()
        self.invoice_number = f"INV-{id(self)}"
        self.tax_rate: float = 0.0
        self.discount = 0.0
        self.discount_type = 'flat'

    def add_item(self, item):
        self.items.append(item)

    def set_tax_rate(self, rate):
        self.tax_rate = rate

    def set_discount(self, amount, discount_type):
        self.discount = amount
        self.discount_type = discount_type

def calculate_subtotal(items):
    return sum(item.price_cal() for item in items)

def apply_discount(subtotal, discount, discount_type):
    return subtotal * (1 - discount) if discount_type == 'percentage' else subtotal - discount

def apply_tax(amount, tax_rate):
    return amount * (1 + tax_rate)

def generate_pdf(invoice, filename=None, signature_img=None, notes=None, terms=None, currency='USD'):
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    from reportlab.lib.colors import HexColor
    import os

    YELLOW = HexColor("#FFD700")
    BLUE = HexColor("#193A7C")
    WHITE = HexColor("#FFFFFF")
    width, height = letter

    # Main grid widths for header, items-table, footer
    colWidths = [2*inch, 2.19*inch, 1*inch, 1.01*inch, 1.15*inch]
    table_width = sum(colWidths)

    def format_currency(amount):
        if currency == 'INR':
            return f"₹{amount:,.2f}"
        else:
            return f"${amount:,.2f}"

    if filename is None:
        filename = f"invoice_{invoice.invoice_number}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=36, bottomMargin=36)
    elements = []

    # -------- HEADER -----------
    logo_path = "logo.png"
    logo = Image(logo_path, width=1.60*inch, height=1.10*inch) if os.path.exists(logo_path) else ""
    left_content = [
        Paragraph('<b>INVOICE</b>', ParagraphStyle('InvoiceTitle', fontName='Helvetica-Bold', fontSize=41, textColor=YELLOW, alignment=TA_LEFT)),
        Spacer(2, 32),
        Paragraph(
            f'<font size=14 color="white">Invoice #: <b>{invoice.invoice_number}</b><br/>Due Date: <b>{invoice.invoice_date.strftime("%d-%m-%Y")}</b><br/>Invoice Date: <b>{invoice.invoice_date.strftime("%d-%m-%Y")}</b></font>',
            ParagraphStyle('SubHead', fontName='Helvetica', fontSize=10, textColor=WHITE, alignment=TA_LEFT)
        ),
    ]
    header_table = Table(
        [[left_content, logo]],
        colWidths=[table_width - 1.52*inch, 1.52*inch], rowHeights=[1.52*inch]
    )
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BLUE),
        ('VALIGN', (0,0), (0,0), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('LEFTPADDING', (0,0), (0,0), 16),
        ('TOPPADDING', (0,0), (0,0), 6),
        ('RIGHTPADDING', (1,0), (1,0), 16),
        ('BOTTOMPADDING', (0,0), (1,0), 12),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 15))

    # -------- BILL TO / BILL FROM -----------
    bt_style = ParagraphStyle('BillBold', fontName='Helvetica-Bold', fontSize=12)
    normal_style = ParagraphStyle('BillNorm', fontName='Helvetica', fontSize=11)
    bill_table = Table([
        [Paragraph("Bill To:", bt_style), "", Paragraph("Bill From:", bt_style), ""],
        [Paragraph(invoice.client.name or "", normal_style), "", Paragraph("Shivohini TechAI", normal_style), ""],
        [Paragraph(f"Contact: {invoice.client.contact}" if invoice.client.contact else "", normal_style), "", Paragraph("Contact: +91 7688929473", normal_style), ""],
        [Paragraph(f"Email: {invoice.client.email}" if invoice.client.email else "", normal_style), "", Paragraph("Email: bhatiagunjan27@gmail.com", normal_style), ""],
        [Paragraph(invoice.client.address or "", normal_style), "", Paragraph("", normal_style), ""]
    ], colWidths=[3*inch, 0.19*inch, 3*inch, 0.1*inch], rowHeights=[18]*5)
    bill_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
    ]))
    elements.append(bill_table)
    elements.append(Spacer(1, 15))

    # -------- ITEM TABLE -----------
    table_headers = [
        Paragraph('<b>Item Name</b>', ParagraphStyle('tHead', fontName='Helvetica-Bold', fontSize=13, textColor=YELLOW, alignment=TA_CENTER)),
        Paragraph('<b>Description</b>', ParagraphStyle('tHead', fontName='Helvetica-Bold', fontSize=13, textColor=YELLOW, alignment=TA_CENTER)),
        Paragraph('<b>Price</b>', ParagraphStyle('tHead', fontName='Helvetica-Bold', fontSize=13, textColor=YELLOW, alignment=TA_CENTER)),
        Paragraph('<b>Quantity</b>', ParagraphStyle('tHead', fontName='Helvetica-Bold', fontSize=13, textColor=YELLOW, alignment=TA_CENTER)),
        Paragraph('<b>Total</b>', ParagraphStyle('tHead', fontName='Helvetica-Bold', fontSize=13, textColor=YELLOW, alignment=TA_CENTER)),
    ]
    item_data = [table_headers]
    for item in invoice.items:
        desc = ", ".join(item.charge_types or []) if item.charge_types else "-"
        row = [
            Paragraph(item.name, ParagraphStyle('tabval', alignment=TA_CENTER, fontName='Helvetica', fontSize=11)),
            Paragraph(desc, ParagraphStyle('tabval', alignment=TA_CENTER, fontName='Helvetica', fontSize=11)),
            Paragraph(format_currency(item.price), ParagraphStyle('tabval', alignment=TA_CENTER, fontName='Helvetica', fontSize=11)),
            Paragraph(str(item.qty), ParagraphStyle('tabval', alignment=TA_CENTER, fontName='Helvetica', fontSize=11)),
            Paragraph(format_currency(item.price_cal()), ParagraphStyle('tabval', alignment=TA_CENTER, fontName='Helvetica', fontSize=11)),
        ]
        item_data.append(row)
    while len(item_data) < 7:
        item_data.append([Paragraph("", normal_style)] * 5)
    item_table = Table(
        item_data,
        colWidths=colWidths, rowHeights=[21]*len(item_data)
    )
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BLUE),
        ('BOX', (0,0), (-1,-1), 1.1, BLUE),
        ('GRID', (0,0), (-1,-1), 0.8, BLUE),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(item_table)
    elements.append(Spacer(1, 10))

    # ---------- TOTALS SUMMARY TABLE ------------
    subtotal = calculate_subtotal(invoice.items)
    discounted = apply_discount(subtotal, invoice.discount, invoice.discount_type)
    total = apply_tax(discounted, invoice.tax_rate)
    tax_display = "{:.2f}%".format(invoice.tax_rate * 100)

    amt_rows = [
        [Paragraph('<b>Subtotal:</b>', bt_style), Paragraph(format_currency(subtotal), normal_style)],
        [Paragraph('<b>Tax:</b>', bt_style), Paragraph(tax_display, normal_style)],
        [
            Paragraph('<b><font color="{}">Amount Due:</font></b>'.format(YELLOW.hexval()),
                      ParagraphStyle('tdue', alignment=TA_CENTER, fontName="Helvetica-Bold", fontSize=13, textColor=YELLOW)),
            Paragraph('<b><font color="{}">{}</font></b>'.format(YELLOW.hexval(), format_currency(total)),
                      ParagraphStyle('tduev', alignment=TA_CENTER, fontName="Helvetica-Bold", fontSize=13, textColor=YELLOW))
        ],
    ]
    amt_table = Table(amt_rows, colWidths=[1.45*inch,1.44*inch], rowHeights=[21,21,21])
    amt_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, BLUE),
        ('GRID', (0,0), (-1,-1), 0.5, BLUE),
        ('FONTNAME', (0,2), (-1,2), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (0,-1), 'RIGHT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('ALIGN', (0,2), (1,2), 'CENTER'),
        ('BACKGROUND', (0,2), (-1,2), BLUE),
        ('TEXTCOLOR', (0,2), (1,2), YELLOW),
    ]))
    elements.append(Table([[amt_table]], colWidths=[table_width], style=[('ALIGN', (0,0), (-1,-1), 'RIGHT')]))
    elements.append(Spacer(1, 16))

    # -------- FOOTER --------
    notes = notes or [""]
    terms = terms or [""]
    nfoot = Paragraph('<b>Notes:</b><br/>' + '<br/>'.join(notes) +
                      '<br/><br/><b>Terms & Conditions:</b><br/>' + '<br/>'.join(terms), normal_style)

    rfoot = []
    if signature_img and os.path.exists(signature_img):
        rfoot.append(Image(signature_img, width=1.7*inch, height=0.48*inch))
    rfoot.append(Spacer(1, 7))
    rfoot.append(Paragraph('<b>Signature</b>', ParagraphStyle('sign', fontName='Helvetica-Bold', fontSize=12, alignment=TA_CENTER)))

    elements.append(
        Table([[nfoot, rfoot]], colWidths=[5*inch, 2*inch], style=[
            ('VALIGN', (0,0), (0,0), 'TOP'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ('LEFTPADDING', (0,1), (0,1), 1),
            ('TOPPADDING', (0,0), (1,0), 15),
            ('BOTTOMPADDING', (0,0), (1,0), 6),
        ])
    )
    elements.append(Spacer(1, 15))

    # -------- BOTTOM BLUE BORDER --------
    class BlueFooterLine(Flowable):
        def __init__(self, width, ypos=0, thickness=40):
            Flowable.__init__(self)
            self.width = width
            self.ypos = ypos
            self.thickness = thickness
        def draw(self):
            self.canv.setStrokeColor(BLUE)
            self.canv.setLineWidth(self.thickness)
            self.canv.line(0, self.ypos, self.width, self.ypos)
    elements.append(BlueFooterLine(table_width, 3, 3))
    elements.append(Spacer(1, 2))

    doc.build(elements)
    return filename
