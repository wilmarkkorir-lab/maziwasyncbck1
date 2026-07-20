import requests
from decouple import config


class MpesaPayment:

    def __init__(self):
        self.consumer_key = config('MPESA_CONSUMER_KEY')
        self.consumer_secret = config('MPESA_CONSUMER_SECRET')
        self.initiator = config('MPESA_INITIATOR')
        self.security_credential = config('MPESA_SECURITY_CREDENTIAL')
        self.callback_url = config('MPESA_CALLBACK_URL')
        self.token_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        self.payment_url = "https://sandbox.safaricom.co.ke/mpesa/b2b/v1/paymentrequest"

    def get_token(self):
        response = requests.get(
            self.token_url,
            auth=requests.auth.HTTPBasicAuth(self.consumer_key, self.consumer_secret)
        )
        return response.json()["access_token"]

    def pay_farmer(self, phone, amount):
        token = self.get_token()
        payload = {
            "Initiator": self.initiator,
            "SecurityCredential": self.security_credential,
            "CommandID": "BusinessPayToBulk",
            "Amount": amount,
            "PartyA": "600989",
            "PartyB": "600000",
            "SenderIdentifierType": "4",
            "RecieverIdentifierType": "4",
            "AccountReference": "MILK",
            "Requester": phone,
            "Remarks": "Milk payment",
            "QueueTimeOutURL": self.callback_url,
            "ResultURL": self.callback_url,
        }
        response = requests.post(
            self.payment_url,
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        )
        return response.json()
