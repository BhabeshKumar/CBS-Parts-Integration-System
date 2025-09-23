"""
Smartsheet Column Mapping for CBS Automation
This file maps the actual column names in your Smartsheet sheets.
"""

# =============================================================================
# ORDERS INTAKE SHEET COLUMNS
# =============================================================================
ORDERS_INTAKE_COLUMNS = {
    "quote_id": "Quote ID",
    "buyer_name": "Buyer's Name",
    "priority": "Priority",
    "quotation_update": "Quotation Update",
    "order_status": "Order Status",
    "quantity": "Quantity Required",
    "part_no": "Part No.",
    "part_description": "Part Description",
    "delivery_address": "Delivery Address",
    "buyer_mobile": "Buyer's Mobile No.",
    "buyer_email": "Buyer's Email Address",
    "order_date": "Order Date",
    "required_date": "Required-By Date",
    "assigned_to": "Assigned to",
    "additional_notes": "Additional Notes",
    "created_date": "Created Date",
    "quotation_link": "Quotation Link",
    "quote_generated_date": "Quote Generated Date"
}

# =============================================================================
# SALES AND WORKS ORDERS SHEET COLUMNS
# =============================================================================
SALES_WORKS_ORDERS_COLUMNS = {
    "buyer_name": "Buyer's Name",
    "sales_order_no": "Sales Order No.",
    "supplier_po": "Supplier's Purchase Order No.",
    "status": "S/W Order Status",
    "part_no": "Part No.",
    "part_description": "Part Description",
    "delivery_address": "Delivery Address",
    "buyer_mobile": "Buyer's Mobile Number",
    "buyer_email": "Buyer's Email Address",
    "created_date": "Creat... Date"
}

# =============================================================================
# STATUS VALUES (Your actual status values)
# =============================================================================
PRIORITY_VALUES = {
    "high": "High",
    "medium": "Medium", 
    "low": "Low"
}

QUOTATION_STATUS_VALUES = {
    "not_started": "Not Started",
    "in_progress": "In Progress",
    "quotation_prepared": "Quotation Prepared, Awaiting Approval",
    "quotation_approved": "Quotation Approved",
    "quotation_won": "Quotation Won"
}

REVIEW_STATUS_VALUES = {
    "draft": "Draft",
    "under_review": "Under Review",
    "approved": "Approved",
    "final": "Final"
}

ORDER_STATUS_VALUES = {
    "new": "New",
    "in_progress": "In Progress",
    "blocked": "Blocked",
    "ordered_from_supplier": "Ordered from Supplier",
    "received_from_supplier": "Received from Supplier",
    "arranged_for_delivery": "Arranged for Delivery",
    "work_in_progress": "Work in Progress"
}

# =============================================================================
# WORKFLOW MAPPING
# =============================================================================
WORKFLOW_TRANSITIONS = {
    # New request workflow
    "new_request": {
        "from_status": "New",
        "to_status": "In Progress",
        "priority": "Medium",
        "quotation_status": "Not Started"
    },
    
    # Quotation workflow
    "quotation_prepared": {
        "from_status": "In Progress",
        "to_status": "In Progress",
        "quotation_status": "Quotation Prepared, Awaiting Approval"
    },
    
    "quotation_approved": {
        "from_status": "In Progress",
        "to_status": "In Progress",
        "quotation_status": "Quotation Approved"
    },
    
    "quotation_won": {
        "from_status": "In Progress",
        "to_status": "In Progress",
        "quotation_status": "Quotation Won"
    },
    
    # Production workflow
    "ordered_from_supplier": {
        "from_status": "In Progress",
        "to_status": "Ordered from Supplier"
    },
    
    "received_from_supplier": {
        "from_status": "Ordered from Supplier",
        "to_status": "Received from Supplier"
    },
    
    "work_in_progress": {
        "from_status": "Received from Supplier",
        "to_status": "Work in Progress"
    },
    
    "arranged_for_delivery": {
        "from_status": "Work in Progress",
        "to_status": "Arranged for Delivery"
    }
}

# =============================================================================
# BUSINESS RULES
# =============================================================================
BUSINESS_RULES = {
    "default_priority": "Medium",
    "default_quotation_status": "Not Started",
    "default_order_status": "New",
    "quotation_validity_days": 30,
    "default_payment_terms_days": 30,
    "default_lead_time_days": 14,
    "quote_ref_prefix": "Q",
    "so_number_prefix": "SO"
}

# =============================================================================
# COLUMN ID CACHE (Will be populated at runtime)
# =============================================================================
COLUMN_ID_CACHE = {
    "orders_intake": {},
    "sales_works_orders": {}
}

def get_column_name(sheet_type: str, field_name: str) -> str:
    """Get the actual column name from the mapping."""
    if sheet_type == "orders_intake":
        return ORDERS_INTAKE_COLUMNS.get(field_name, field_name)
    elif sheet_type == "sales_works_orders":
        return SALES_WORKS_ORDERS_COLUMNS.get(field_name, field_name)
    else:
        return field_name

def get_status_value(status_type: str, value_key: str) -> str:
    """Get the actual status value from the mapping."""
    if status_type == "priority":
        return PRIORITY_VALUES.get(value_key, value_key)
    elif status_type == "quotation":
        return QUOTATION_STATUS_VALUES.get(value_key, value_key)
    elif status_type == "order":
        return ORDER_STATUS_VALUES.get(value_key, value_key)
    else:
        return value_key

def get_workflow_transition(from_status: str, action: str) -> dict:
    """Get workflow transition details."""
    return WORKFLOW_TRANSITIONS.get(action, {})

def get_business_rule(rule_name: str) -> str:
    """Get business rule value."""
    return BUSINESS_RULES.get(rule_name, "")
