import requests
import json
import sys
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_text_api(receipt_text: str) -> Optional[Dict[str, Any]]:
    """
    Test the text-based API endpoint
    
    Args:
        receipt_text: The text of the receipt to parse
        
    Returns:
        The parsed receipt data or None if an error occurred
    """
    url = "http://localhost:5000/api/parse"
    
    try:
        logger.info("Sending request to text API endpoint...")
        response = requests.post(
            url,
            json={"receipt_text": receipt_text},
            headers={"Content-Type": "application/json"}
        )
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Parse the JSON response
        data = response.json()
        
        logger.info("Successfully received response from API")
        return data
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending request to API: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                logger.error(f"API error response: {error_data}")
            except:
                logger.error(f"API error status code: {e.response.status_code}")
                logger.error(f"API error text: {e.response.text}")
        return None
    
def test_pdf_api(pdf_path: str) -> Optional[Dict[str, Any]]:
    """
    Test the PDF upload API endpoint
    
    Args:
        pdf_path: Path to the PDF file to upload
        
    Returns:
        The parsed receipt data or None if an error occurred
    """
    url = "http://localhost:5000/api/upload_pdf"
    
    try:
        logger.info(f"Uploading PDF file: {pdf_path}")
        
        with open(pdf_path, 'rb') as pdf_file:
            files = {'file': (pdf_path, pdf_file, 'application/pdf')}
            response = requests.post(url, files=files)
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Parse the JSON response
        data = response.json()
        
        logger.info("Successfully received response from API")
        return data
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending request to API: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                logger.error(f"API error response: {error_data}")
            except:
                logger.error(f"API error status code: {e.response.status_code}")
                logger.error(f"API error text: {e.response.text}")
        return None
    except FileNotFoundError:
        logger.error(f"PDF file not found: {pdf_path}")
        return None

def print_parsed_data(data: Dict[str, Any]) -> None:
    """Print the parsed data in a formatted way"""
    if data is None:
        logger.error("No data to print")
        return
    
    print("\n" + "="*50 + " API RESULT " + "="*50 + "\n")
    print(json.dumps(data, indent=2))
    print("\n" + "="*120 + "\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_api.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    # Test the PDF upload API
    pdf_result = test_pdf_api(pdf_path)
    if pdf_result:
        print_parsed_data(pdf_result)
    
    # Read the PDF text for the text API test
    from pypdf import PdfReader
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        # Test the text API
        text_result = test_text_api(text)
        if text_result:
            print_parsed_data(text_result)
    
    except Exception as e:
        logger.error(f"Error reading PDF file: {str(e)}")