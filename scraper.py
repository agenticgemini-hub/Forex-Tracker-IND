import requests
from bs4 import BeautifulSoup
import io
import pdfplumber

def get_axis_bank_usd_buy():
    url = "https://application.axis.bank.in/webforms/corporatecardrate/index.aspx"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=10, verify=False)
        res.raise_for_status()
        soup = BeautifulSoup(res.content, 'html.parser')
        table = soup.find('table')
        if not table:
            print("No table found on Axis Bank page.")
            return None
        
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) > 2:
                # Typically Currency Name, Code, Buy, Sell, etc.
                text_content = [c.text.strip() for c in cols]
                if 'USD' in text_content or 'US Dollar' in text_content:
                    rates = []
                    for val in text_content[2:]:
                        try:
                            rates.append(float(val))
                        except ValueError:
                            pass
                    
                    # The 7th valid rate (index 6) corresponds to CCY BUY
                    if len(rates) > 6:
                        rate = rates[6]
                        if rate > 0:
                            return rate
        return None
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error fetching Axis bank rate: {e}")
        return None

def get_hdfc_bank_usd_buy():
    url = "https://www.hdfc.bank.in/content/dam/hdfcbankpws/in/en/personal-banking/discover-products/interest-rates/hdfc-bank-treasury-forex-card-rates.pdf"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=10, verify=False)
        res.raise_for_status()
        
        with pdfplumber.open(io.BytesIO(res.content)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    for line in text.split('\n'):
                        parts = line.split()
                        if 'USD' in parts and any(term in line for term in ['United States Dollar', 'US Dollar', 'UnitedStatesDollar']):
                            # It usually looks like: UnitedStatesDollar USD 93.20 98.22 ...
                            try:
                                # Find the index of 'USD'
                                idx = parts.index('USD')
                                # Extract all floats after 'USD'
                                rates = []
                                for part in parts[idx + 1:]:
                                    try:
                                        rates.append(float(part))
                                    except ValueError:
                                        pass
                                
                                # The 7th rate (index 6) corresponds to CCY BUY
                                if len(rates) > 6:
                                    rate = rates[6]
                                    if rate > 50 and rate < 150: # Sanity check for USD INR
                                        return rate
                            except (ValueError, IndexError):
                                pass
        return None
    except Exception as e:
        print(f"Error fetching HDFC bank rate: {e}")
        return None

if __name__ == "__main__":
    print(f"Axis Bank USD Buy: {get_axis_bank_usd_buy()}")
    print(f"HDFC Bank USD Buy: {get_hdfc_bank_usd_buy()}")
