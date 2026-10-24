
# Vendor Payment Audit Analytics
# Test 1: Identify potential duplicate payments

payments = [
    {"vendor": "Vendor A", "invoice": "INV001", "amount": 1500},
    {"vendor": "Vendor B", "invoice": "INV002", "amount": 2200},
    {"vendor": "Vendor A", "invoice": "INV001", "amount": 1500},
    {"vendor": "Vendor C", "invoice": "INV003", "amount": 800},
]

seen = set()

for payment in payments:
    key = (
        payment["vendor"],
        payment["invoice"],
        payment["amount"]
    )

    if key in seen:
        print("Potential duplicate payment found:", payment)
    else:
        seen.add(key)
