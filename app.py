from flask import Flask, request, jsonify, send_file
import pdfplumber
import xml.etree.ElementTree as ET
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def extract_transactions(pdf_path):
    transactions = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines = text.split("\n")
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 3:
                        try:
                            date = parts[0]  # Adjust index based on actual format
                            description = " ".join(parts[1:-1])
                            amount = parts[-1].replace(",", "")
                            transactions.append({"date": date, "description": description, "amount": amount})
                        except:
                            pass
    return transactions

def create_tally_xml(transactions, output_file):
    root = ET.Element("ENVELOPE")
    header = ET.SubElement(root, "HEADER")
    ET.SubElement(header, "TALLYREQUEST").text = "Import Data"
    
    body = ET.SubElement(root, "BODY")
    import_data = ET.SubElement(body, "IMPORTDATA")
    tally_message = ET.SubElement(import_data, "TALLYMESSAGE")

    for txn in transactions:
        voucher = ET.SubElement(tally_message, "VOUCHER")
        ET.SubElement(voucher, "DATE").text = txn["date"]
        ET.SubElement(voucher, "PARTICULARS").text = txn["description"]
        ET.SubElement(voucher, "AMOUNT").text = txn["amount"]

    tree = ET.ElementTree(root)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)

@app.route("/upload", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    transactions = extract_transactions(file_path)
    
    if not transactions:
        return jsonify({"error": "No transactions found"}), 400

    xml_file = os.path.join(OUTPUT_FOLDER, f"{file.filename}.xml")
    create_tally_xml(transactions, xml_file)

    return send_file(xml_file, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
