from flask import Flask, request, jsonify, render_template_string
from flask_mail import Mail, Message
from fpdf import FPDF
import requests
import os
import threading

app = Flask(__name__)

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.office365.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'Bot_donotreply@dynatecsmv.no'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'NeverEverReply1995'  # Replace with your email password
app.config['MAIL_DEFAULT_SENDER'] = 'Bot_donotreply@dynatecsmv.no'  # Replace with your email

mail = Mail(app)

class PDF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='A4')

    def header(self):
        self.image('logo.jpg', x=self.w - 90, y=10, w=80)

    def footer(self):
        self.set_draw_color(0, 176, 80)  # RGB for #00B050
        self.set_line_width(2)
        self.rect(5, 5, 200, self.h / 2 - 5)

def create_pallet_label(data_array, filename):
    pdf = PDF()
    pdf.set_auto_page_break(auto=False)

    def clean_text(text):
        return text.replace('�', '') if text else text
   # Sort the data array by PositionID
    data_array.sort(key=lambda x: x.get('PositionID', ''))

    # Loop through the data array to create individual pages
    for data in data_array:
        pdf.add_page()

        print(data)
        # QR Code generation
        qr_code_data = clean_text(data.get('qr', 'DEFAULT_STORAGE_ID'))
        qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={qr_code_data}"
        qr_code_response = requests.get(qr_code_url)

        if qr_code_response.status_code == 200:
            qr_code_filename = f"qr_code_{qr_code_data}.png"
            with open(qr_code_filename, 'wb') as f:
                f.write(qr_code_response.content)

        # Move the QR code slightly below by adjusting the y coordinate (originally y=10)
        pdf.image(qr_code_filename, x=10, y=20, w=50, h=50)  # Adjust 'y' value to move it down
        os.remove(qr_code_filename)
       # Set font and position for "Customer + Order"
        pdf.set_font('Arial', 'B', 40)
        pdf.set_xy(10, 80)  # Adjust y-coordinate as needed
        pdf.cell(0, 10, clean_text(data.get('Customer + Order', 'DEFAULT_ORDER')), ln=True)

        # Set font and position for "Content" directly below "Customer + Order"
        pdf.set_font('Arial', '', 25)
        pdf.set_xy(10, pdf.get_y() + 5)  # Adjust the y-coordinate to move "Content" up
        content = clean_text(data.get('Content', 'Default Content'))
        pdf.multi_cell(0, 8, content)



        # Adjusting remaining space
        remaining_space = (pdf.h / 2) - pdf.get_y() - 20
        if remaining_space > 0:
            pdf.set_y(pdf.get_y() + remaining_space / 2)

        # Set font for "Owner" and "Created By"
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 8, f"Owner: {clean_text(data.get('Owner', 'Default Owner'))}", ln=True)
        pdf.cell(0, 8, f"Created By: {clean_text(data.get('Created By', 'Default Creator'))}", ln=True)

        pdf.set_y(pdf.get_y() + 10)  # Additional spacing

        label_revision = clean_text(data.get('LabelRevision', 'DEFAULT_LABEL_REVISION'))
        position_id = clean_text(data.get('PositionID', 'DEFAULT_POSITION_ID'))
        pdf.set_xy(10, 10)  # Set to upper left corner (x=10, y=10)
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, f"{label_revision} - {position_id}", 0, 1, 'L')  # Align left

        mail_address = clean_text(data.get('MailAdress', 'default@mail.com'))

    pdf.output(filename)
    return mail_address, [clean_text(data['StorageID']) for data in data_array]
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
                body { display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f8f9fa; font-family: Arial, sans-serif; text-align: center; }
                h1 { font-size: 3em; color: #343a40; }
                p { font-size: 1.5em; color: #6c757d; }
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


@app.route('/fetch-and-generate', methods=['GET'])
def fetch_and_generate():
    try:
        glide_api_url = 'https://functions.prod.internal.glideapps.com/api/apps/WALpghAXNz7kVRH9HFdx/tables/native-table-7HWStsovzmSyVBveLMUe/rows'
        headers = {
            'user-agent': 'Make/production',
            'authorization': 'Bearer 4ba1af06-5ac2-4346-a5b6-b9ded23fafa8',  # Replace with your actual token
            'x-glide-client-id': '3def4919-730b-4dac-9a18-5478c9d4ea0c'
        }

        response = requests.get(glide_api_url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            print(data)
            data_array = []
            for row in data.get('data', {}).get('rows', []):
                entry_dict = {
                    'Customer + Order': row.get('Name', 'DEFAULT_ORDER'),
                    'StorageID': row.get('$rowID', 'DEFAULT_STORAGE_ID'),
                    'MailAdress': row.get('383W6', 'default@mail.com'),
                    'Owner': row.get('loQhD', 'Default Owner'),
                    'qr': row.get('knlbN', 'DEFAULT_STORAGE_ID'),
                    'Created By': row.get('dVWZJ', 'Default Creator'),
                    'Content': row.get('PyIlB', 'Default Content'),
                    'LabelRevision': row.get('edrDV', 'DEFAULT_LABEL_REVISION'),
                    'PositionID': row.get('LVx14', 'DEFAULT_POSITION_ID'),
                }
                data_array.append(entry_dict)

            pdf_filename = 'pallet_label.pdf'
            mail_address, row_ids_to_delete = create_pallet_label(data_array, pdf_filename)

            # Start email sending in a separate thread
            email_thread = threading.Thread(target=send_email_with_attachment, args=('ahsanahmad4654@gmail.com', pdf_filename))
            email_thread.start()

            # Delete the rows after starting the email thread
            # delete_rows(row_ids_to_delete)

            return jsonify({"message": f"PDF created successfully at {pdf_filename}", "email": mail_address}), 200
        else:
            return jsonify({"error": "Failed to fetch data from Glide API", "status_code": response.status_code}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def send_email_with_attachment(to_email, pdf_filename):
    try:
        with app.app_context():
            msg = Message("Pallet Label PDF", recipients=[to_email])
            msg.body = "Please find the attached pallet label PDF."
            with app.open_resource(pdf_filename) as pdf:
                msg.attach(pdf_filename, "application/pdf", pdf.read())
            mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {str(e)}")

def delete_rows(row_ids):
    try:
        glide_api_url = 'https://functions.prod.internal.glideapps.com/api/apps/WALpghAXNz7kVRH9HFdx/tables/native-table-7HWStsovzmSyVBveLMUe/rows'
        headers = {
            'user-agent': 'Make/production',
            'authorization': 'Bearer 4ba1af06-5ac2-4346-a5b6-b9ded23fafa8',  # Replace with your actual token
            'x-glide-client-id': '3def4919-730b-4dac-9a18-5478c9d4ea0c',
            'content-type': 'application/json'
        }

        # Send the DELETE request with the row IDs
        response = requests.delete(glide_api_url, headers=headers, json=row_ids)

        if response.status_code != 200:
            print(f"Failed to delete rows: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error deleting rows: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
