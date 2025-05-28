import logging
from receipt_parser import parse_walmart_receipt
from pypdf import PdfReader
import json

# Set up logging
logging.basicConfig(level=logging.DEBUG)

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file"""
    try:
        logging.info(f"Reading PDF file: {pdf_path}")
        
        # Create a PDF reader object
        reader = PdfReader(pdf_path)
        
        # Extract text from each page
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        return text
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {str(e)}")
        return None

def test_parse_receipt(pdf_path):
    """Test the receipt parser with a PDF file"""
    # Extract text from PDF
    receipt_text = extract_text_from_pdf(pdf_path)
    
    if receipt_text:
        logging.info("Extracted text from PDF, now parsing...")
        
        # Parse the receipt text
        try:
            result = parse_walmart_receipt(receipt_text)
            
            # Print the result
            print("\n" + "="*50 + " PARSED RESULT " + "="*50 + "\n")
            print(json.dumps(result, indent=2))
            print("\n" + "="*120 + "\n")
            
            return result
        except Exception as e:
            logging.error(f"Error parsing receipt: {str(e)}")
            return None
    else:
        logging.error("Failed to extract text from PDF")
        return None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python test_parser.py <path_to_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    test_parse_receipt(pdf_path)