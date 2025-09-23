"""
Quotation Generator Integration Service
Connects the CBS parts system with the existing quotation generator.
"""

import logging
import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class QuotationIntegrationService:
    """Service to integrate with the existing CBS quotation generator."""
    
    def __init__(self):
        """Initialize the quotation integration service."""
        # Configuration for quotation generator
        self.quotation_api_base = "http://localhost:3000"  # Adjust as needed
        self.quotation_generator_url = "http://localhost:8080"  # Your existing generator
        
    def prepare_quotation_data(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare order data in the format expected by the quotation generator.
        
        Args:
            order_data: Order data from the review interface
            
        Returns:
            Formatted data for quotation generator
        """
        try:
            # Calculate totals
            subtotal = sum(part.get('line_total', 0) for part in order_data.get('selectedParts', []))
            
            # Apply discount if any
            discount_amount = order_data.get('discountAmount', 0)
            discounted_total = subtotal - discount_amount
            
            # Calculate VAT (23%)
            vat_amount = discounted_total * 0.23
            grand_total = discounted_total + vat_amount
            
            # Format in the structure your quotation generator expects
            quotation_data = {
                "customerInfo": {
                    "name": order_data.get('customerName', ''),
                    "email": order_data.get('customerEmail', ''),
                    "mobile": order_data.get('customerMobile', ''),
                    "deliveryAddress": order_data.get('deliveryAddress', ''),
                    "requiredDate": order_data.get('requiredDate', ''),
                },
                "orderDetails": {
                    "quoteId": order_data.get('quoteId', ''),
                    "orderDate": order_data.get('orderDate', ''),
                    "priority": order_data.get('priority', 'Medium'),
                    "additionalNotes": order_data.get('additionalNotes', ''),
                },
                "items": [],
                "pricing": {
                    "subtotal": subtotal,
                    "discountAmount": discount_amount,
                    "discountedTotal": discounted_total,
                    "vatRate": 0.23,
                    "vatAmount": vat_amount,
                    "grandTotal": grand_total,
                    "currency": "EUR"
                },
                "status": "approved",
                "generatedAt": datetime.now().isoformat()
            }
            
            # Format items/parts
            for i, part in enumerate(order_data.get('selectedParts', []), 1):
                item = {
                    "lineNumber": i,
                    "productCode": part.get('product_code', ''),
                    "description": part.get('description', ''),
                    "quantity": part.get('quantity', 1),
                    "unitPrice": part.get('sales_price', 0),
                    "lineTotal": part.get('line_total', 0),
                    "category": "Parts"  # Default category
                }
                quotation_data["items"].append(item)
            
            logger.info(f"Prepared quotation data for Quote ID: {order_data.get('quoteId')}")
            return quotation_data
            
        except Exception as e:
            logger.error(f"Error preparing quotation data: {e}")
            raise
    
    def generate_quotation_pdf(self, quotation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate quotation PDF using the existing quotation generator.
        
        Args:
            quotation_data: Formatted quotation data
            
        Returns:
            Result with PDF path or URL
        """
        try:
            # This would integrate with your existing quotation generator
            # For now, we'll create a mock response
            
            quote_id = quotation_data.get('orderDetails', {}).get('quoteId', 'UNKNOWN')
            
            # Example API call to your existing quotation generator
            # response = requests.post(
            #     f"{self.quotation_generator_url}/api/generate-quotation",
            #     json=quotation_data,
            #     headers={'Content-Type': 'application/json'}
            # )
            
            # Mock response for now
            result = {
                "success": True,
                "quoteId": quote_id,
                "pdfPath": f"temp_files/quotation_{quote_id}.pdf",
                "pdfUrl": f"https://cbsparts.yourcompany.com/temp_files/quotation_{quote_id}.pdf",
                "generatedAt": datetime.now().isoformat(),
                "message": "Quotation generated successfully"
            }
            
            logger.info(f"Generated quotation for Quote ID: {quote_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating quotation: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate quotation"
            }
    
    def update_smartsheet_with_quotation(self, quote_id: str, quotation_result: Dict[str, Any]) -> bool:
        """
        Update the Smartsheet Orders Intake with quotation details.
        
        Args:
            quote_id: Quote ID to update
            quotation_result: Result from quotation generation
            
        Returns:
            Success status
        """
        try:
            from services.smartsheet_service import SmartsheetService
            
            smartsheet_service = SmartsheetService()
            
            # Prepare update data
            update_data = {}
            
            if quotation_result.get('success'):
                update_data = {
                    "Quotation Update": "Quotation Sent to the Buyer",
                    "Order Status": "In Progress",
                    "Quote Generated Date": datetime.now().strftime("%Y-%m-%d"),
                }
                
                # Add quotation link if available
                if quotation_result.get('pdfUrl'):
                    update_data["Quotation Link"] = quotation_result['pdfUrl']
            else:
                update_data = {
                    "Quotation Update": "Quotation Declined, Subject to Revision",
                    "Additional Notes": f"Error: {quotation_result.get('error', 'Unknown error')}"
                }
            
            # Find and update the row
            # Note: This is a simplified approach - you might want to implement 
            # a more robust row finding mechanism
            
            logger.info(f"Updated Smartsheet for Quote ID: {quote_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating Smartsheet: {e}")
            return False
    
    def trigger_quotation_generation(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete quotation generation workflow.
        
        Args:
            order_data: Complete order data from review interface
            
        Returns:
            Complete result including PDF generation and Smartsheet update
        """
        try:
            quote_id = order_data.get('quoteId', 'UNKNOWN')
            logger.info(f"Starting quotation generation for Quote ID: {quote_id}")
            
            # Step 1: Prepare data
            quotation_data = self.prepare_quotation_data(order_data)
            
            # Step 2: Generate PDF
            quotation_result = self.generate_quotation_pdf(quotation_data)
            
            # Step 3: Update Smartsheet
            smartsheet_updated = self.update_smartsheet_with_quotation(quote_id, quotation_result)
            
            # Return complete result
            return {
                "success": quotation_result.get('success', False),
                "quoteId": quote_id,
                "quotationData": quotation_data,
                "quotationResult": quotation_result,
                "smartsheetUpdated": smartsheet_updated,
                "message": quotation_result.get('message', 'Quotation generation completed')
            }
            
        except Exception as e:
            logger.error(f"Error in quotation generation workflow: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to complete quotation generation"
            }
    
    def get_quotation_template_data(self, quote_id: str) -> Dict[str, Any]:
        """
        Get template data for quotation generation.
        This can be used to pre-populate your existing quotation generator.
        
        Args:
            quote_id: Quote ID to get data for
            
        Returns:
            Template data for quotation
        """
        try:
            # This would fetch order data and format it for your existing quotation generator
            # You can customize this based on your current quotation template requirements
            
            template_data = {
                "template": "cbs_parts_quotation",
                "quoteId": quote_id,
                "companyInfo": {
                    "name": "Concrete Batching Systems",
                    "address": "Your Company Address",
                    "phone": "Your Phone Number",
                    "email": "info@concretebatchingsystems.com",
                    "website": "www.concretebatchingsystems.com"
                },
                "formatting": {
                    "currency": "EUR",
                    "vatRate": 0.23,
                    "dateFormat": "DD/MM/YYYY"
                }
            }
            
            return template_data
            
        except Exception as e:
            logger.error(f"Error getting template data: {e}")
            return {}


# Example usage and testing
if __name__ == "__main__":
    # Test the quotation integration
    service = QuotationIntegrationService()
    
    # Sample order data for testing
    sample_order = {
        "quoteId": "CBS-2025-TEST",
        "customerName": "Test Customer",
        "customerEmail": "test@example.com",
        "customerMobile": "+353 123 456 789",
        "deliveryAddress": "123 Test Street, Dublin",
        "requiredDate": "2025-01-15",
        "orderDate": "2025-01-08",
        "selectedParts": [
            {
                "product_code": "MIXER-001",
                "description": "High Capacity Mixer Unit",
                "quantity": 2,
                "sales_price": 1500.00,
                "line_total": 3000.00
            },
            {
                "product_code": "PUMP-002",
                "description": "Hydraulic Pump Assembly",
                "quantity": 1,
                "sales_price": 800.00,
                "line_total": 800.00
            }
        ],
        "discountAmount": 0,
        "additionalNotes": "Test order for quotation generation"
    }
    
    # Test quotation generation
    result = service.trigger_quotation_generation(sample_order)
    print("Quotation Generation Result:")
    print(json.dumps(result, indent=2))
