from flask import Flask, request, jsonify, render_template_string
from fpdf import FPDF
import requests
import os
from urllib.parse import quote as url_quote  # Updated import

app = Flask(__name__)

class PDF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='A4')

    def header(self):
        self.image('logo.jpg', x=self.w - 90, y=10, w=80)

    def footer(self):
        self.set_draw_color(0, 176, 80)
        self.set_line_width(2)
        self.rect(5, 5, 200, self.h / 2 - 5)

def create_pallet_label(data_array, filename):
    pdf = PDF()
    pdf.set_auto_page_break(auto=False)
    pdf.set_font('Arial', '', 12)

    for data in data_array:
        pdf.add_page()
        qr_code_data = data.get('Customer + Order', 'DEFAULT_ORDER')
        qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={qr_code_data}"
        qr_code_response = requests.get(qr_code_url)

        if qr_code_response.status_code == 200:
            qr_code_filename = f"qr_code_{qr_code_data}.png"
            with open(qr_code_filename, 'wb') as f:
                f.write(qr_code_response.content)

            pdf.image(qr_code_filename, x=10, y=10, w=50, h=50)
            os.remove(qr_code_filename)

        pdf.set_font('Arial', 'B', 16)
        pdf.set_xy(10, 70)
        pdf.cell(0, 10, f"Customer + Order: {data.get('Customer + Order', 'DEFAULT_ORDER')}", ln=True)

        pdf.set_font('Arial', 'B', 14)
        pdf.set_xy(10, pdf.get_y() + 10)
        pdf.cell(0, 10, "Content", ln=True)
        pdf.set_font('Arial', '', 12)
        content = data.get('Content', 'Default Content')
        pdf.multi_cell(0, 8, content)

        label_revision = data.get('LabelRevision', 'Default LabelRevision')
        position_id = data.get('PositionID', 'Default Position ID')
        pdf.set_xy(10, pdf.get_y() + 5)
        pdf.cell(0, 10, f"LabelRevision: {label_revision} - Position ID: {position_id}", ln=True)

        remaining_space = (pdf.h / 2) - pdf.get_y() - 20
        if remaining_space > 0:
            pdf.set_y(pdf.get_y() + remaining_space / 2)

        pdf.cell(0, 8, f"Owner: {data.get('Owner', 'Default Owner')}", ln=True)
        pdf.cell(0, 8, f"Created By: {data.get('Created By', 'Default Creator')}", ln=True)

        storage_id = data.get('StorageID', 'Default StorageID')
        pdf.cell(0, 8, f"StorageID: {storage_id}", ln=True)

        mail_address = data.get('MailAdress', 'default@mail.com')

    pdf.output(filename)
    return mail_address

@app.route('/')
def home():
    return render_template_string('''
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Coming Soon</title>
            <style>
                body {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    background-color: #f8f9fa;
                    font-family: Arial, sans-serif;
                    text-align: center;
                }
                h1 {
                    font-size: 3em;
                    color: #343a40;
                }
                p {
                    font-size: 1.5em;
                    color: #6c757d;
                }
            </style>
        </head>
        <body>
            <div>
                <h1>Coming Soon</h1>
                <p>We are working hard to get this site up and running. Stay tuned!</p>
            </div>
        </body>
        </html>
    ''')

@app.route('/generate-pallet-label', methods=['POST'])
def generate_pallet_label():
    try:
        data_array = request.json['entries']
        pdf_filename = 'pallet_label.pdf'
        mail_address = create_pallet_label(data_array, pdf_filename)
        
        return jsonify({"message": f"PDF created successfully at {pdf_filename}", "email": mail_address}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
