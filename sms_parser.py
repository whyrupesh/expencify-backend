import spacy
import re
import pandas as pd

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")

def extract_transaction_info(text):
    """Extract transaction details from a single SMS."""
    doc = nlp(text)
    
    # Define patterns
    account_pattern = r"A/C \*?(\d{4,})|A/C (\d{10})|A/c XX(\d{4})"
    amount_pattern = r"Rs\.?\s?\d+(?:,\d{3})*(?:\.\d{2})?|INR\s?\d+(?:,\d{3})*(?:\.\d{2})?"
    date_pattern = r"(?:on\s+)?(\d{1,2}-\d{1,2}-\d{4}|\d{2}/\d{2}/\d{4})"
    time_pattern = r"(\d{1,2}:\d{2}(?:\s?[APMapm]{2})?)"
    
    # Search patterns
    account_number = re.search(account_pattern, text)
    amount = re.search(amount_pattern, text)
    date = re.search(date_pattern, text)
    time = re.search(time_pattern, text)
    
    # Determine transaction type
    transaction_type = "debit" if re.search(r"debited|purchase|spent|withdrawn", text, re.IGNORECASE) else \
                       "credit" if re.search(r"credited|deposit|received", text, re.IGNORECASE) else None
    
    # Extract receiver (if any)
    receiver = None
    potential_receivers = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    if potential_receivers:
        receiver = potential_receivers[-1]

    return {
        "Receiver": receiver,
        "Account Number": account_number.group(0) if account_number else None,
        "Amount": amount.group(0) if amount else None,
        "Date": date.group(1) if date else None,
        "Time": time.group(1) if time else None,
        "Transaction Type": transaction_type
    }

def preprocess_text(text):
    """Lowercase and clean text."""
    return re.sub(r'[^a-z\s]', '', text.lower()) if text else None

categories = {
    'food': ['starbucks', 'mcdonalds', 'dominos'],
    'clothing': ['nike', 'h&m', 'adidas'],
    'accessories': ['watch', 'jewelry'],
    'Bank Transfer': ['funds transfer']
}

def classify_receiver(receiver):
    """Classify the payment receiver into a category."""
    if receiver:
        for category, keywords in categories.items():
            if any(keyword.lower() in receiver.lower() for keyword in keywords):
                return category
    return 'other'

def is_transactional_message(text):
    """Determine if an SMS is a transactional message."""
    # Keywords indicating a bank transaction
    transaction_keywords = ["debited", "credited", "A/C", "balance", "withdrawn", "deposit"]
    return any(keyword.lower() in text.lower() for keyword in transaction_keywords)

def parse_sms_list(sms_list):
    """Parse a list of SMS messages and return the results."""
    filtered_sms = [sms['body'] for sms in sms_list if is_transactional_message(sms['body'])]
    
    extracted_data = [extract_transaction_info(sms) for sms in filtered_sms]
    df = pd.DataFrame(extracted_data)
    
    # Check if 'Receiver' column exists to avoid KeyError
    if 'Receiver' in df.columns:
        df['Receiver'] = df['Receiver'].apply(preprocess_text)
        df['Category'] = df['Receiver'].apply(classify_receiver)
    else:
        df['Category'] = 'unknown'

    return df.to_dict(orient='records')
