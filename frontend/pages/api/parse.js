import axios from 'axios';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Forward the request to the Flask backend
    const response = await axios.post('http://localhost:5000/api/parse', req.body);
    
    // Return the response from the Flask backend
    return res.status(200).json(response.data);
  } catch (error) {
    console.error('Error calling Flask backend:', error);
    return res.status(500).json({ 
      error: error.response?.data?.error || 'Failed to process receipt' 
    });
  }
}