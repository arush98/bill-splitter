import re
import json
import logging
import google.generativeai as genai
import os

def parse_walmart_receipt(receipt_text):
    """
    Parse a Walmart receipt text and extract items with their prices.
    
    Args:
        receipt_text (str): The raw text from a Walmart receipt PDF
    
    Returns:
        dict: A dictionary with an 'items' key containing a list of item dictionaries
              Each item has 'name' and 'price' keys
    """
    logging.debug("Starting to parse receipt text")
    
    # Try to use Gemini API if the key is available
    gemini_api_key = os.environ.get("GEMINI_API_KEY", None)
    
    if gemini_api_key:
        try:
            logging.debug("Using Gemini API for parsing")
            return parse_with_gemini(receipt_text, gemini_api_key)
        except Exception as e:
            logging.error(f"Gemini API error: {str(e)}. Falling back to regex parsing.")
    else:
        logging.debug("No Gemini API key found, using regex parsing")
    
    # Initialize the result structure
    result = {"items": []}
    
    # Split the receipt into lines and clean them
    lines = receipt_text.split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    
    # Regular expression patterns to match item lines with prices
    # Pattern 1: Standard format with "Shopped Qty X"
    pattern1 = re.compile(r'^(.+?)\s+(?:Shopped|Unavailable)\s+Qty\s+\d+\s+\$([\d.]+)$')
    # Pattern 2: Format with "Weight-adjusted Qty X"
    pattern2 = re.compile(r'^(.+?)\s+Weight-adjusted\s+Qty\s+\d+\s+\$([\d.]+)$')
    # Pattern 3: Tax line
    tax_pattern = re.compile(r'^Tax\s+\$([\d.]+)$')
    
    # Process each line
    for line in lines:
        # Skip header/footer lines and non-item lines
        if 'Order#' in line or 'Subtotal' in line or 'Total' in line or 'Driver tip' in line:
            continue
        if 'delivery' in line.lower() or 'payment method' in line:
            continue
        
        # Try to match tax pattern first
        tax_match = tax_pattern.match(line)
        if tax_match:
            tax_amount = float(tax_match.group(1).strip())
            result["items"].append({
                "name": "Tax",
                "price": tax_amount
            })
            logging.debug(f"Extracted tax: ${tax_amount}")
            continue
        
        # Try to match item patterns
        match = pattern1.match(line) or pattern2.match(line)
        if match:
            item_name = match.group(1).strip()
            item_price = float(match.group(2).strip())
            
            # Add the item to our result
            result["items"].append({
                "name": item_name,
                "price": item_price
            })
            logging.debug(f"Extracted item: {item_name} - ${item_price}")
    
    # If we didn't find any items using the strict patterns, try a more flexible approach
    if not result["items"]:
        logging.debug("No items found with strict patterns, trying alternate approach")
        
        # Alternative pattern to handle different receipt formats
        # This looks for a product description followed by a price
        alt_pattern = re.compile(r'(.+?)\s+\$([\d.]+)\s*$')
        
        for line in lines:
            # Skip lines that are clearly not items
            if 'Order#' in line or 'Subtotal' in line or 'Total' in line:
                continue
            
            match = alt_pattern.search(line)
            if match:
                item_name = match.group(1).strip()
                # Skip if it contains keywords that suggest it's not an item
                if any(keyword in item_name.lower() for keyword in ['subtotal', 'total', 'delivery', 'tip']):
                    continue
                
                try:
                    item_price = float(match.group(2).strip())
                    result["items"].append({
                        "name": item_name,
                        "price": item_price
                    })
                    logging.debug(f"Extracted item (alt method): {item_name} - ${item_price}")
                except ValueError:
                    logging.debug(f"Failed to convert price to float: {match.group(2)}")
    
    logging.debug(f"Parsed {len(result['items'])} items from receipt")
    return result

def parse_with_gemini(receipt_text, api_key):
    """
    Use the Gemini API to parse a Walmart receipt.
    
    Args:
        receipt_text (str): The raw text from a Walmart receipt PDF
        api_key (str): The Gemini API key
        
    Returns:
        dict: A dictionary with an 'items' key containing a list of item dictionaries
    """
    # Configure the Gemini API
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    # Define the prompt for the Gemini API
    prompt = f"""
    You are a JSON extraction assistant specialized in parsing retail receipts.  
    Given the raw text of a Walmart PDF receipt, produce *only* valid JSON with this structure:

    {{
      "items": [
        {{ "name": "<exact item description>", "price": <numeric price> }},
        …
      ]
    }}

    Rules:
    1. **Item entries only**: Extract each purchased line‑item as its own object.  
    2. **Fields**:
       - **name** (string): the product description exactly as it appears (including multi‑word names).  
       - **price** (number): the item's price, stripped of "$" or commas.  
    3. **Ignore everything else**: store header/footer, address, date/time, payment method, subtotals, taxes, totals, coupons, returns, loyalty points—omit them.  
    4. **No commentary**: output only the JSON object above, nothing else.  
    5. **Strict JSON**: ensure parsable JSON (no trailing commas, no markdown).  

    Here's the receipt text to parse:
    """
    
    # Call the Gemini API
    response = model.generate_content(prompt + receipt_text)
    response_text = response.text
    
    # Extract JSON from the response
    # Remove any markdown code block indicators (```json or ```)
    json_str = response_text.strip()
    if json_str.startswith("```"):
        json_str = json_str[json_str.find("\n")+1:]
    if json_str.endswith("```"):
        json_str = json_str[:json_str.rfind("```")]
    
    json_str = json_str.strip()
    
    # Parse the JSON
    try:
        parsed_data = json.loads(json_str)
        logging.debug(f"Successfully parsed with Gemini: {len(parsed_data['items'])} items found")
        return parsed_data
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse Gemini response as JSON: {str(e)}")
        logging.debug(f"Response was: {response_text}")
        raise ValueError("Invalid JSON response from Gemini API")

def validate_json_output(data):
    """
    Validate that the output is valid JSON according to our schema.
    
    Args:
        data (dict): The parsed receipt data
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Check basic structure
    if not isinstance(data, dict) or 'items' not in data:
        return False
    
    # Check items is a list
    if not isinstance(data['items'], list):
        return False
    
    # Check each item has the required fields
    for item in data['items']:
        if not isinstance(item, dict):
            return False
        if 'name' not in item or 'price' not in item:
            return False
        if not isinstance(item['name'], str) or not isinstance(item['price'], (int, float)):
            return False
    
    # Validate it can be serialized to JSON
    try:
        json.dumps(data)
        return True
    except (TypeError, OverflowError):
        return False
