"""
SQLite Parts Service for Fast Local Search
Syncs with Smartsheet every 24 hours
"""
import sqlite3
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import os
import json

logger = logging.getLogger(__name__)

class SQLitePartsService:
    def __init__(self, db_path: str = "data/parts_cache.db"):
        self.db_path = db_path
        self.last_sync = None
        self.sync_interval = timedelta(hours=24)  # 24 hours
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Check if we need to sync
        asyncio.create_task(self._check_and_sync())
    
    def _init_database(self):
        """Initialize SQLite database with parts table"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create parts table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS parts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_code TEXT UNIQUE,
                        description TEXT,
                        sales_price REAL,
                        cost_price REAL,
                        stock_level TEXT,
                        category TEXT,
                        supplier TEXT,
                        notes TEXT,
                        row_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes for fast searching
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_code ON parts(product_code)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_description ON parts(description)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON parts(category)')
                
                # Create sync tracking table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sync_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sync_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        parts_count INTEGER,
                        status TEXT,
                        message TEXT
                    )
                ''')
                
                conn.commit()
                logger.info("SQLite parts database initialized")
                
        except Exception as e:
            logger.error(f"Error initializing SQLite database: {e}")
    
    async def _check_and_sync(self):
        """Check if sync is needed and perform it"""
        try:
            # Check last sync time
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT MAX(sync_time) FROM sync_log WHERE status = "success"')
                result = cursor.fetchone()
                
                if result[0]:
                    self.last_sync = datetime.fromisoformat(result[0])
                
            # Check if sync is needed
            if (not self.last_sync or 
                datetime.now() - self.last_sync > self.sync_interval):
                logger.info("Parts database sync needed, starting sync...")
                await self.sync_with_smartsheet()
            else:
                logger.info(f"Parts database is up to date (last sync: {self.last_sync})")
                
        except Exception as e:
            logger.error(f"Error checking sync status: {e}")
    
    async def sync_with_smartsheet(self):
        """Sync parts data from Smartsheet to SQLite"""
        try:
            logger.info("🔄 Starting Smartsheet to SQLite sync...")
            
            # Get parts from Smartsheet
            from src.services.smartsheet_service import SmartsheetService
            from config.cbs_parts_config import CBS_PARTS_SHEET_ID
            
            service = SmartsheetService()
            sheet = service.client.Sheets.get_sheet(CBS_PARTS_SHEET_ID)
            
            if not sheet or not sheet.rows:
                logger.warning("No parts data found in Smartsheet")
                return False
            
            # Get column mapping
            columns = {col.title: col.id for col in sheet.columns}
            
            parts_data = []
            for row in sheet.rows:
                row_data = {}
                for cell in row.cells:
                    col_title = next((title for title, col_id in columns.items() if col_id == cell.column_id), None)
                    if col_title and cell.value:
                        row_data[col_title] = str(cell.value)
                
                # Format part data
                part = {
                    'product_code': row_data.get('Product Code', ''),
                    'description': row_data.get('Description', ''),
                    'sales_price': self._parse_price(row_data.get('Sales Price', '0')),
                    'cost_price': self._parse_price(row_data.get('Cost Price', '0')),
                    'stock_level': row_data.get('Stock Level', 'Unknown'),
                    'category': row_data.get('Category', ''),
                    'supplier': row_data.get('Supplier', ''),
                    'notes': row_data.get('Notes', ''),
                    'row_id': row.id
                }
                
                if part['product_code']:  # Only add parts with valid product codes
                    parts_data.append(part)
            
            # Update SQLite database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Clear existing data
                cursor.execute('DELETE FROM parts')
                
                # Insert new data
                for part in parts_data:
                    cursor.execute('''
                        INSERT INTO parts 
                        (product_code, description, sales_price, cost_price, stock_level, 
                         category, supplier, notes, row_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        part['product_code'],
                        part['description'],
                        part['sales_price'],
                        part['cost_price'],
                        part['stock_level'],
                        part['category'],
                        part['supplier'],
                        part['notes'],
                        part['row_id']
                    ))
                
                # Log successful sync
                cursor.execute('''
                    INSERT INTO sync_log (parts_count, status, message)
                    VALUES (?, ?, ?)
                ''', (len(parts_data), 'success', f'Synced {len(parts_data)} parts from Smartsheet'))
                
                conn.commit()
                
            self.last_sync = datetime.now()
            logger.info(f"✅ Successfully synced {len(parts_data)} parts to SQLite database")
            return True
            
        except Exception as e:
            # Log failed sync
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO sync_log (parts_count, status, message)
                        VALUES (?, ?, ?)
                    ''', (0, 'failed', str(e)))
                    conn.commit()
            except:
                pass
                
            logger.error(f"❌ Failed to sync parts from Smartsheet: {e}")
            return False
    
    def search_parts(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Fast search for parts in SQLite database"""
        try:
            query_lower = query.lower()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Search in product code, description, and category
                cursor.execute('''
                    SELECT product_code, description, sales_price, cost_price, 
                           stock_level, category, supplier, notes, row_id
                    FROM parts 
                    WHERE LOWER(product_code) LIKE ? 
                       OR LOWER(description) LIKE ?
                       OR LOWER(category) LIKE ?
                       OR LOWER(supplier) LIKE ?
                    ORDER BY 
                        CASE 
                            WHEN LOWER(product_code) = ? THEN 1
                            WHEN LOWER(product_code) LIKE ? THEN 2
                            WHEN LOWER(description) LIKE ? THEN 3
                            ELSE 4
                        END,
                        product_code
                    LIMIT ?
                ''', (
                    f'%{query_lower}%',  # product_code LIKE
                    f'%{query_lower}%',  # description LIKE
                    f'%{query_lower}%',  # category LIKE
                    f'%{query_lower}%',  # supplier LIKE
                    query_lower,         # exact match priority
                    f'{query_lower}%',   # starts with priority
                    f'%{query_lower}%',  # description priority
                    limit
                ))
                
                results = cursor.fetchall()
                
                parts = []
                for row in results:
                    part = {
                        'product_code': row[0],
                        'description': row[1],
                        'sales_price': row[2] or 0,
                        'cost_price': row[3] or 0,
                        'stock_level': row[4] or 'Unknown',
                        'category': row[5] or '',
                        'supplier': row[6] or '',
                        'notes': row[7] or '',
                        'row_id': row[8]
                    }
                    parts.append(part)
                
                logger.info(f"SQLite search: '{query}' returned {len(parts)} results")
                return parts
                
        except Exception as e:
            logger.error(f"Error searching SQLite parts database: {e}")
            return []
    
    def get_part_by_code(self, product_code: str) -> Optional[Dict[str, Any]]:
        """Get a specific part by product code"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT product_code, description, sales_price, cost_price, 
                           stock_level, category, supplier, notes, row_id
                    FROM parts 
                    WHERE LOWER(product_code) = LOWER(?)
                ''', (product_code,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'product_code': row[0],
                        'description': row[1],
                        'sales_price': row[2] or 0,
                        'cost_price': row[3] or 0,
                        'stock_level': row[4] or 'Unknown',
                        'category': row[5] or '',
                        'supplier': row[6] or '',
                        'notes': row[7] or '',
                        'row_id': row[8]
                    }
            return None
            
        except Exception as e:
            logger.error(f"Error getting part by code: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get parts count
                cursor.execute('SELECT COUNT(*) FROM parts')
                parts_count = cursor.fetchone()[0]
                
                # Get last sync info
                cursor.execute('''
                    SELECT sync_time, status, message 
                    FROM sync_log 
                    ORDER BY sync_time DESC 
                    LIMIT 1
                ''')
                last_sync_row = cursor.fetchone()
                
                return {
                    'parts_count': parts_count,
                    'last_sync': last_sync_row[0] if last_sync_row else None,
                    'last_sync_status': last_sync_row[1] if last_sync_row else None,
                    'last_sync_message': last_sync_row[2] if last_sync_row else None,
                    'database_size': os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                }
                
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def _parse_price(self, price_str: str) -> float:
        """Parse price string to float"""
        try:
            # Remove currency symbols and spaces
            cleaned = str(price_str).replace('€', '').replace('$', '').replace(',', '').strip()
            return float(cleaned) if cleaned else 0.0
        except (ValueError, TypeError):
            return 0.0

# Global instance
sqlite_parts_service = SQLitePartsService()
