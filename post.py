import requests

url = "http://127.0.0.1:8000/patients/create"
payload = {
    "pFullName": "John Doe",
    "pDob": "1990-01-01",
    "pSex": "Male",
    "pPhone": "1234567890",
    "pEmail": "johndoe@example.com",
    "pAddress": "123 Main St, Anytown, USA",
    "providerName": "Aetna"
}

response = requests.post(url, json=payload)


print(response.text)