import os
import json
import logging
import tempfile
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from receipt_parser import parse_walmart_receipt
from werkzeug.utils import secure_filename
from pypdf import PdfReader
from models import db, Distribution, DistributionUser
from nanoid import generate

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__, 
    static_folder='static',
    template_folder='templates',
    static_url_path='')
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

# Configure database
if os.environ.get('VERCEL'):
    # Use SQLite file in /tmp for Vercel
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/receipts.db"
else:
    # Use local SQLite database for development
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///receipts.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize database with app
db.init_app(app)

# Ensure tables exist on every request (for serverless)
@app.before_request
def before_request():
    try:
        with app.app_context():
            db.create_all()
    except Exception as e:
        logging.error(f"Database initialization error: {str(e)}")
        return jsonify({"error": "Database initialization failed"}), 500

# Enable CORS
CORS(app)

# Create upload directory
if os.environ.get('VERCEL'):
    # Use /tmp for Vercel
    UPLOAD_FOLDER = '/tmp/uploads'
else:
    # Use local directory for development
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tmp', 'uploads')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
logging.info(f"Upload folder set to: {UPLOAD_FOLDER}")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Render the main page with the receipt parsing interface."""
    try:
        return render_template('index.html')
    except Exception as e:
        logging.error(f"Error rendering index: {str(e)}")
        return jsonify({"error": "Failed to render page"}), 500

@app.route('/api/parse', methods=['POST'])
def parse_receipt():
    """API endpoint to parse a Walmart receipt and return structured JSON data."""
    try:
        if not request.json or 'receipt_text' not in request.json:
            return jsonify({'error': 'No receipt text provided'}), 400
        
        receipt_text = request.json['receipt_text']
        if not receipt_text.strip():
            return jsonify({'error': 'Receipt text is empty'}), 400
        
        # Parse the receipt text
        parsed_data = parse_walmart_receipt(receipt_text)
        
        # Add nanoid to the parsed data
        parsed_data['receipt_id'] = generate(size=10)
        
        # Return the parsed data
        return jsonify(parsed_data)
    
    except Exception as e:
        logging.error(f"Error parsing receipt: {str(e)}")
        return jsonify({'error': f'Failed to parse receipt: {str(e)}'}), 500

@app.route('/api/upload_pdf', methods=['POST'])
def upload_pdf():
    """API endpoint to upload and parse a PDF receipt."""
    logging.debug("Received upload_pdf request")
    try:
        # Check if file part exists
        if 'file' not in request.files:
            logging.debug("No file part in the request")
            return jsonify({'error': 'No file part in the request'}), 400
        
        file = request.files['file']
        logging.debug(f"Received file: {file.filename}")
        
        # Check if file is empty
        if file.filename == '':
            logging.debug("Empty filename")
            return jsonify({'error': 'No file selected'}), 400
        
        # Check if file is allowed
        if not allowed_file(file.filename):
            logging.debug(f"Invalid file type: {file.filename}")
            return jsonify({'error': 'File type not allowed. Only PDF files are accepted.'}), 400
        
        # Create upload directory if it doesn't exist
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Save the file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        logging.debug(f"Saving file to: {filepath}")
        
        try:
            file.save(filepath)
        except Exception as e:
            logging.error(f"Error saving file: {str(e)}")
            return jsonify({'error': f'Failed to save file: {str(e)}'}), 500
        
        # Extract text from PDF
        text = ""
        try:
            pdf = PdfReader(filepath)
            logging.debug(f"PDF has {len(pdf.pages)} pages")
            for page in pdf.pages:
                text += page.extract_text() + "\n"
            logging.debug(f"Extracted {len(text)} characters of text")
        except Exception as e:
            logging.error(f"Error extracting text from PDF: {str(e)}")
            return jsonify({'error': f'Failed to extract text from PDF: {str(e)}'}), 500
        
        # Parse the receipt text
        logging.debug("Parsing receipt text with parser")
        parsed_data = parse_walmart_receipt(text)
        
        # Add nanoid to the parsed data
        parsed_data['receipt_id'] = generate(size=10)
        logging.debug(f"Generated receipt ID: {parsed_data['receipt_id']}")
        
        # Remove the temp file
        try:
            os.remove(filepath)
            logging.debug(f"Removed temp file: {filepath}")
        except Exception as e:
            logging.warning(f"Failed to remove temp file: {str(e)}")
        
        # Ensure we're returning valid JSON
        response = jsonify(parsed_data)
        response.headers['Content-Type'] = 'application/json'
        logging.debug("Returning JSON response")
        return response
    
    except Exception as e:
        logging.error(f"Error processing PDF: {str(e)}")
        error_response = jsonify({'error': f'Failed to process PDF: {str(e)}'})
        error_response.headers['Content-Type'] = 'application/json'
        return error_response, 500

@app.route('/api/save_distribution', methods=['POST'])
def save_distribution():
    """API endpoint to save the cost distribution to the database."""
    logging.debug("Received save_distribution request")
    try:
        # Get the distribution data from the request
        if not request.json:
            logging.debug("No JSON data in the request")
            return jsonify({'error': 'No distribution data provided'}), 400
        
        data = request.json
        logging.debug(f"Received distribution data: {json.dumps(data)[:200]}...")
        
        # Check required fields
        if 'users' not in data or not data['users']:
            logging.debug("No users in the distribution data")
            return jsonify({'error': 'No users found in distribution data'}), 400
        
        if 'items' not in data or not data['items']:
            logging.debug("No items in the distribution data")
            return jsonify({'error': 'No items found in distribution data'}), 400
        
        if 'total' not in data:
            logging.debug("No total amount in the distribution data")
            return jsonify({'error': 'No total amount found in distribution data'}), 400
        
        # Generate a unique distribution ID
        distribution_id = generate(size=10)
        
        # Create distribution record
        distribution = Distribution(
            receipt_name=data.get('receipt_name', 'Walmart Receipt'),
            total_amount=float(data['total']),
            distribution_data=json.dumps(data),
            distribution_id=distribution_id
        )
        
        # Add to database
        db.session.add(distribution)
        db.session.flush()  # To get the ID
        
        # Create distribution user records
        for user in data['users']:
            # Find user's items and calculate total
            user_items = []
            user_total = 0
            
            for item in data['items']:
                if user['id'] in item.get('users', []):
                    # Calculate this user's share for the item
                    user_count = len(item.get('users', []))
                    if user_count > 0:
                        share = item['price'] / user_count
                        user_total += share
                        user_items.append({
                            'name': item['name'],
                            'price': item['price'],
                            'share': share
                        })
            
            # Create user distribution record
            dist_user = DistributionUser(
                distribution_id=distribution.id,
                user_name=user['name'],
                user_identifier=user['id'],
                amount=user_total,
                items_json=json.dumps(user_items)
            )
            db.session.add(dist_user)
        
        # Commit all changes
        db.session.commit()
        logging.debug(f"Distribution saved with ID: {distribution_id}")
        
        return jsonify({
            'success': True,
            'distribution_id': distribution_id,
            'message': 'Distribution saved successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error saving distribution: {str(e)}")
        return jsonify({'error': f'Failed to save distribution: {str(e)}'}), 500

@app.route('/api/distributions', methods=['GET'])
def get_distributions():
    """API endpoint to get all saved distributions."""
    try:
        distributions = Distribution.query.order_by(Distribution.created_at.desc()).all()
        return jsonify({
            'distributions': [d.to_dict() for d in distributions]
        })
    except Exception as e:
        logging.error(f"Error getting distributions: {str(e)}")
        return jsonify({'error': f'Failed to get distributions: {str(e)}'}), 500

@app.route('/favicon.ico')
def favicon():
    """Serve the favicon."""
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/analytics')
def analytics():
    """Render the analytics page with previous purchase data."""
    # Get all distributions ordered by date (newest first)
    distributions = Distribution.query.order_by(Distribution.created_at.desc()).all()
    
    # Create user expenditure data for charts
    user_data = {}
    weekly_data = {}
    monthly_data = {}
    now = datetime.utcnow()
    
    # Get distributions from the last 30 days for weekly/monthly views
    thirty_days_ago = now - timedelta(days=30)
    recent_distributions = Distribution.query.filter(Distribution.created_at >= thirty_days_ago).all()
    
    # Process each distribution
    for dist in recent_distributions:
        # Extract month and week 
        month = dist.created_at.strftime('%Y-%m')
        week = dist.created_at.strftime('%Y-W%U')
        
        # Setup data structures if they don't exist yet
        if month not in monthly_data:
            monthly_data[month] = {}
        if week not in weekly_data:
            weekly_data[week] = {}
            
        # Process user data for this distribution
        for user in dist.users:
            # Add to user totals
            if user.user_name not in user_data:
                user_data[user.user_name] = 0
            user_data[user.user_name] += user.amount
            
            # Add to monthly data
            if user.user_name not in monthly_data[month]:
                monthly_data[month][user.user_name] = 0
            monthly_data[month][user.user_name] += user.amount
            
            # Add to weekly data
            if user.user_name not in weekly_data[week]:
                weekly_data[week][user.user_name] = 0
            weekly_data[week][user.user_name] += user.amount
    
    # Convert to sorted arrays for the charts
    user_totals = sorted([(name, amount) for name, amount in user_data.items()], 
                         key=lambda x: x[1], reverse=True)
    
    # Sort weeks and months chronologically
    sorted_weeks = sorted(weekly_data.keys())
    sorted_months = sorted(monthly_data.keys())
    
    # Extract all unique user names for consistent chart colors
    all_users = set(user_data.keys())
    
    return render_template('analytics.html', 
                           distributions=distributions,
                           user_totals=user_totals,
                           weekly_data=weekly_data,
                           monthly_data=monthly_data,
                           sorted_weeks=sorted_weeks,
                           sorted_months=sorted_months,
                           all_users=all_users)

@app.route('/share/<distribution_id>')
def shared_distribution(distribution_id):
    """Render the main page with a pre-loaded distribution."""
    # Get the distribution from the database
    distribution = Distribution.query.filter_by(distribution_id=distribution_id).first_or_404()
    return render_template('index.html', shared_distribution=distribution.to_dict())

@app.route('/api/distribution/<distribution_id>', methods=['GET'])
def get_distribution(distribution_id):
    """API endpoint to get a specific distribution by ID."""
    try:
        distribution = Distribution.query.filter_by(distribution_id=distribution_id).first_or_404()
        return jsonify(distribution.to_dict())
    except Exception as e:
        logging.error(f"Error getting distribution: {str(e)}")
        return jsonify({'error': f'Failed to get distribution: {str(e)}'}), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({"error": "Internal server error"}), 500

# This is important for Vercel
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
