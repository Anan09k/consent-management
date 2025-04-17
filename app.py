from flask import Flask, request, jsonify, render_template
import uuid
import datetime
import hashlib

app = Flask(__name__)

# --- Consent Class ---
class Consent:
    def __init__(self, user_id, data_types, purpose, expiry_date=None):
        self.user_id = user_id
        self.data_types = data_types
        self.purpose = purpose
        self.expiry_date = expiry_date or (datetime.datetime.utcnow() + datetime.timedelta(days=365))
        self.consent_id = self.generate_consent_id()
        self.timestamp = datetime.datetime.utcnow()
        self.status = "active"

    def generate_consent_id(self):
        data_string = f"{self.user_id}{''.join(self.data_types)}{self.purpose}{self.expiry_date}"
        return hashlib.sha256(data_string.encode()).hexdigest()

    def is_valid(self):
        if self.status != "active":
            return False
        if datetime.datetime.utcnow() > self.expiry_date:
            self.status = "expired"
            return False
        return True

    def revoke(self):
        self.status = "revoked"


consents = {}

def validate_consent(consent_id, consents):
    if consent_id not in consents:
        return False, "Consent ID not found"
    consent = consents[consent_id]
    if not consent.is_valid():
        return False, f"Consent {consent.status}"
    return True, "Consent is valid"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/consent', methods=['POST'])
def provide_consent():
    data = request.get_json()
    user_id = data.get('userId')
    data_types = data.get('dataTypes')
    purpose = data.get('purpose')

    if not user_id or not data_types or not purpose:
        return jsonify({"error": "Missing required fields"}), 400

    new_consent = Consent(user_id, data_types, purpose)
    consents[new_consent.consent_id] = new_consent
    return jsonify({"consentId": new_consent.consent_id}), 201

@app.route('/validate/<consent_id>')
def validate(consent_id):
    is_valid, reason = validate_consent(consent_id, consents)
    return jsonify({"isValid": is_valid, "reason": reason})

if __name__ == '__main__':
    app.run(debug=True)

