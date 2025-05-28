from datetime import datetime
import json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Define base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

class Distribution(db.Model):
    """
    Stores a receipt distribution among users
    """
    id = db.Column(db.Integer, primary_key=True)
    distribution_id = db.Column(db.String(10), unique=True, nullable=False)  # nanoid
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    receipt_name = db.Column(db.String(255), nullable=True)
    total_amount = db.Column(db.Float, nullable=False)
    distribution_data = db.Column(db.Text, nullable=False)  # JSON string of the full distribution data
    
    # Relationship with DistributionUser
    users = db.relationship('DistributionUser', backref='distribution', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Distribution {self.distribution_id}: ${self.total_amount}>"
    
    def to_dict(self):
        """Convert distribution to dictionary"""
        return {
            'id': self.id,
            'distribution_id': self.distribution_id,
            'created_at': self.created_at.isoformat(),
            'receipt_name': self.receipt_name,
            'total_amount': self.total_amount,
            'distribution_data': json.loads(self.distribution_data),
            'users': [user.to_dict() for user in self.users]
        }


class DistributionUser(db.Model):
    """
    Stores user information for a distribution
    """
    id = db.Column(db.Integer, primary_key=True)
    distribution_id = db.Column(db.Integer, db.ForeignKey('distribution.id'), nullable=False)
    user_name = db.Column(db.String(255), nullable=False)
    user_identifier = db.Column(db.String(50), nullable=False)  # e.g., "user1", "user2", etc.
    amount = db.Column(db.Float, nullable=False)
    items_json = db.Column(db.Text, nullable=False)  # JSON string of items assigned to this user
    
    def __repr__(self):
        return f"<DistributionUser {self.user_name}: ${self.amount}>"
    
    def to_dict(self):
        """Convert user distribution to dictionary"""
        return {
            'id': self.id,
            'user_name': self.user_name,
            'user_identifier': self.user_identifier,
            'amount': self.amount,
            'items': json.loads(self.items_json)
        }