from flask import Flask, request, jsonify
from fpdf import FPDF
import requests
import os

app = Flask(__name__)

# Function to create shipment label PDF with QR code for each entry
def create_shipment_label(data_array, filename):
    pdf = FPDF(orientation='L', unit='mm', format='A5')  # Set A5 landscape

    for data in data_array:
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        
        # Add header
        pdf.cell(190, 10, txt="Shipment Label", ln=True, align='C')  # Adjust width for landscape
        pdf.ln(10)

        # Add Sender Details
        pdf.set_font('Arial', '', 12)
        pdf.cell(190, 10, txt=f"Sender Name: {data.get('sender_name', 'John Doe')}", ln=True)
        pdf.cell(190, 10, txt=f"Sender Address: {data.get('sender_address', '1234 Elm St, City, Country')}", ln=True)
        pdf.cell(190, 10, txt=f"Sender Email: {data.get('sender_email', 'john@example.com')}", ln=True)
        pdf.cell(190, 10, txt=f"Sender Phone: {data.get('sender_phone', '+1 234 567 890')}", ln=True)
        pdf.ln(10)
        
        # Add Receiver Details
        pdf.cell(190, 10, txt=f"Receiver Name: {data.get('receiver_name', 'Jane Doe')}", ln=True)
        pdf.cell(190, 10, txt=f"Receiver Address: {data.get('receiver_address', '5678 Oak St, Another City, Country')}", ln=True)
        pdf.cell(190, 10, txt=f"Receiver Email: {data.get('receiver_email', 'jane@example.com')}", ln=True)
        pdf.cell(190, 10, txt=f"Receiver Phone: {data.get('receiver_phone', '+1 987 654 321')}", ln=True)
        pdf.ln(10)

        # Add shipment details
        pdf.cell(190, 10, txt=f"Shipment Date: {data.get('shipment_date', '2024-09-23')}", ln=True)
        pdf.cell(190, 10, txt=f"Tracking Number: {data.get('tracking_number', 'TRACK123456')}", ln=True)
        pdf.ln(10)
        
        # Fetch and add QR Code
        qr_code_data = data.get('tracking_number', 'TRACK123456')
        qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={qr_code_data}"
        qr_code_response = requests.get(qr_code_url)
        
        if qr_code_response.status_code == 200:
            qr_code_filename = "qr_code.png"
            with open(qr_code_filename, 'wb') as f:
                f.write(qr_code_response.content)

            # Insert QR code image in PDF (adjusted for landscape)
            pdf.image(qr_code_filename, x=75, y=None, w=50, h=50)
            os.remove(qr_code_filename)  # Remove the QR code image after embedding it
    
    # Save the PDF to file
    pdf.output(filename)

@app.route('/generate-shipment-label', methods=['POST'])
def generate_shipment_label():
    try:
        # Get data from POST request (array of entries)
        data_array = request.json['entries']
        
        # Create PDF file
        pdf_filename = 'shipment_label.pdf'
        create_shipment_label(data_array, pdf_filename)
        
        return jsonify({"message": f"PDF created successfully at {pdf_filename}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
