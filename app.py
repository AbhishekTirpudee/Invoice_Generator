from flask import Flask, render_template, request, jsonify, send_file
from main import Client, Item, Invoice, generate_pdf
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-key')
app.config['UPLOAD_FOLDER'] = './signatures'  # ensure this exists

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_invoice', methods=['POST'])
def create_invoice():
    if 'data' in request.form:
        import json
        data = json.loads(request.form['data'])
    else:
        data = request.json

    signature_path = None
    if 'signature' in request.files:
        file = request.files['signature']
        if file and file.filename:
            filename = secure_filename(file.filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            signature_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(signature_path)

    client = Client(
        name=data['client']['name'],
        email=data['client']['email'],
        address=data['client']['address'],
        contact=data['client'].get('phone')
    )

    invoice = Invoice(client)
    for item_data in data['items']:
        charge_types = item_data.get('charge_types', [])
        charge_amounts = item_data.get('charge_amounts', [])
        max_len = max(len(charge_types), len(charge_amounts))
        charge_types += [''] * (max_len - len(charge_types))
        charge_amounts += [0.0] * (max_len - len(charge_amounts))
        item = Item(
            name=item_data['name'],
            qty=int(item_data['quantity']),
            price=float(item_data['price']),
            charge_types=charge_types,
            charge_amounts=[float(a) for a in charge_amounts]
        )
        invoice.add_item(item)

    if 'tax_rate' in data:
        invoice.set_tax_rate(float(data['tax_rate']))
    if 'discount' in data:
        invoice.set_discount(float(data['discount']), data.get('discount_type', 'flat'))

    # Extract currency option, defaults to 'USD'
    currency = data.get('currency', 'USD')

    pdf_filename = generate_pdf(
        invoice,
        signature_img=signature_path,
        notes=data.get('notes', []),
        terms=data.get('terms', []),
        currency=currency  # pass currency to PDF generator
    )

    if not pdf_filename or not os.path.exists(pdf_filename):
        return jsonify({'success': False, 'message': 'Failed to generate PDF', 'pdf_url': None}), 500

    return jsonify({
        'success': True,
        'invoice_number': invoice.invoice_number,
        'pdf_url': f'/download/{pdf_filename}'
    })

@app.route('/download/<filename>')
def download_file(filename):
    if not os.path.exists(filename):
        return "File not found.", 404
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
