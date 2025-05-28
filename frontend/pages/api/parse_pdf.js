import formidable from 'formidable';
import fs from 'fs';
import axios from 'axios';
import pdfParse from 'pdf-parse';

// Disable the default body parser
export const config = {
  api: {
    bodyParser: false,
  },
};

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Parse form with uploaded file
    const form = formidable({});
    const [fields, files] = await form.parse(req);
    
    if (!files.pdf || files.pdf.length === 0) {
      return res.status(400).json({ error: 'No PDF file uploaded' });
    }
    
    const file = files.pdf[0];
    
    // Read the uploaded PDF file
    const pdfBuffer = fs.readFileSync(file.filepath);
    
    // Extract text from PDF
    const pdfData = await pdfParse(pdfBuffer);
    const receiptText = pdfData.text;
    
    // Process the receipt text with the Gemini API
    const parsedData = await processWithGemini(receiptText);
    
    // Return the parsed data
    res.status(200).json(parsedData);
  } catch (error) {
    console.error('Error processing PDF:', error);
    res.status(500).json({ error: 'Failed to process PDF' });
  }
}

async function processWithGemini(receiptText) {
  try {
    const response = await axios.post('/api/parse', {
      receipt_text: receiptText
    });
    
    return response.data;
  } catch (error) {
    console.error('Error calling Gemini API:', error);
    throw new Error('Failed to process receipt with Gemini');
  }
}