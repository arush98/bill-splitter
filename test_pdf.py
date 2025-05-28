from pypdf import PdfReader
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file"""
    try:
        logging.info(f"Reading PDF file: {pdf_path}")
        
        # Create a PDF reader object
        reader = PdfReader(pdf_path)
        
        # Get the number of pages
        num_pages = len(reader.pages)
        logging.info(f"PDF has {num_pages} pages")
        
        # Extract text from each page
        text = ""
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            text += f"\n--- Page {i+1} ---\n{page_text}\n"
        
        return text
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {str(e)}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_pdf.py <path_to_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    text = extract_text_from_pdf(pdf_path)
    
    print("\n" + "="*50 + " EXTRACTED TEXT " + "="*50 + "\n")
    print(text)
    print("\n" + "="*120 + "\n")