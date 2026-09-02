#!/usr/bin/env python3
"""
AWS RDS Inventory Collector with Database Storage

Collects RDS instance information across multiple AWS regions and accounts,
and stores the data in a MySQL database for centralized inventory management.
"""

import boto3
import argparse
import logging
import mysql.connector
import os
from datetime import datetime
from typing import List, Dict, Any
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from botocore.exceptions import ClientError, NoCredentialsError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RDSInventoryCollector:
    """Collects RDS inventory across multiple AWS regions and accounts."""
    
    def __init__(self, profile: str = None, regions: List[str] = None, store_in_db: bool = False):
        """
        Initialize the RDS Inventory Collector.
        
        Args:
            profile: AWS profile name to use
            regions: List of AWS regions to scan. If None, scans all available regions.
            store_in_db: Whether to store results in database
        """
        self.profile = profile
        self.session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        self.regions = regions or self._get_all_regions()
        self.inventory_data = []
        self.store_in_db = store_in_db
        self.db_connection = None
        
        if self.store_in_db:
            self._connect_to_database()
            self._create_table()
        
    def _get_all_regions(self) -> List[str]:
        """Get all available AWS regions for RDS."""
        try:
            ec2_client = self.session.client('ec2', region_name='us-east-1')
            regions = ec2_client.describe_regions()
            return [region['RegionName'] for region in regions['Regions']]
        except Exception as e:
            logger.warning(f"Could not retrieve all regions: {e}. Using default regions.")
            return ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1']
    
    def _connect_to_database(self):
        """Connect to MySQL database."""
        try:
            db_host = os.getenv('DB_HOST')
            db_user = os.getenv('DB_USER')
            db_password = os.getenv('DB_PASSWORD')
            db_name = os.getenv('DB_NAME')
            
            if not all([db_host, db_user, db_password, db_name]):
                logger.warning("Database credentials not found. Set environment variables:")
                logger.warning("  DB_HOST, DB_USER, DB_PASSWORD, DB_NAME")
                self.store_in_db = False
                return
            
            self.db_connection = mysql.connector.connect(
                host=db_host,
                user=db_user,
                password=db_password,
                database=db_name,
                autocommit=True
            )
            logger.info(f"✅ Successfully connected to database: {db_name}")
        except mysql.connector.Error as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            logger.error("Make sure your database is running and credentials are correct.")
            self.store_in_db = False
    
    def _create_table(self):
        """Create the RDS inventory table if it doesn't exist."""
        if not self.db_connection:
            return
        
        try:
            cursor = self.db_connection.cursor()
            
            create_table_query = """
            CREATE TABLE IF NOT EXISTS rds_inventory (
                id INT AUTO_INCREMENT PRIMARY KEY,
                aws_account_id VARCHAR(50),
                collection_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                region VARCHAR(50),
                db_instance_identifier VARCHAR(255),
                db_instance_class VARCHAR(100),
                engine VARCHAR(50),
                engine_version VARCHAR(50),
                db_instance_status VARCHAR(50),
                master_username VARCHAR(255),
                endpoint_address VARCHAR(255),
                endpoint_port INT,
                allocated_storage INT,
                storage_type VARCHAR(50),
                storage_encrypted BOOLEAN,
                multi_az BOOLEAN,
                availability_zone VARCHAR(100),
                vpc_id VARCHAR(100),
                publicly_accessible BOOLEAN,
                backup_retention_period INT,
                preferred_backup_window VARCHAR(100),
                preferred_maintenance_window VARCHAR(100),
                auto_minor_version_upgrade BOOLEAN,
                license_model VARCHAR(100),
                deletion_protection BOOLEAN,
                iam_database_authentication_enabled BOOLEAN,
                performance_insights_enabled BOOLEAN,
                latest_restorable_time DATETIME,
                instance_create_time DATETIME,
                INDEX idx_region (region),
                INDEX idx_identifier (db_instance_identifier),
                INDEX idx_timestamp (collection_timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            cursor.execute(create_table_query)
            logger.info("✅ Table 'rds_inventory' is ready")
            cursor.close()
        except mysql.connector.Error as e:
            logger.error(f"❌ Error creating table: {e}")
    
    def _insert_into_database(self, instance_data: Dict[str, Any]):
        """Insert RDS instance data in database."""
        if not self.db_connection:
            return
        
        try:
            cursor = self.db_connection.cursor()
            
            insert_query = """
            INSERT INTO rds_inventory (
                aws_account_id, region, db_instance_identifier, db_instance_class,
                engine, engine_version, db_instance_status, master_username,
                endpoint_address, endpoint_port, allocated_storage, storage_type,
                storage_encrypted, multi_az, availability_zone, vpc_id,
                publicly_accessible, backup_retention_period, preferred_backup_window,
                preferred_maintenance_window, auto_minor_version_upgrade, license_model,
                deletion_protection, iam_database_authentication_enabled,
                performance_insights_enabled, latest_restorable_time, instance_create_time
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            
            values = (
                instance_data.get('aws_account_id', 'N/A'),
                instance_data.get('Region'),
                instance_data.get('DBInstanceIdentifier'),
                instance_data.get('DBInstanceClass'),
                instance_data.get('Engine'),
                instance_data.get('EngineVersion'),
                instance_data.get('DBInstanceStatus'),
                instance_data.get('MasterUsername'),
                instance_data.get('Endpoint'),
                instance_data.get('Port'),
                instance_data.get('AllocatedStorage'),
                instance_data.get('StorageType'),
                instance_data.get('StorageEncrypted'),
                instance_data.get('MultiAZ'),
                instance_data.get('AvailabilityZone'),
                instance_data.get('VpcId'),
                instance_data.get('PubliclyAccessible'),
                instance_data.get('BackupRetentionPeriod'),
                instance_data.get('PreferredBackupWindow'),
                instance_data.get('PreferredMaintenanceWindow'),
                instance_data.get('AutoMinorVersionUpgrade'),
                instance_data.get('LicenseModel'),
                instance_data.get('DeletionProtection'),
                instance_data.get('IAMDatabaseAuthenticationEnabled'),
                instance_data.get('PerformanceInsightsEnabled'),
                instance_data.get('LatestRestorableTime'),
                instance_data.get('InstanceCreateTime')
            )
            
            cursor.execute(insert_query, values)
            logger.debug(f"Inserted: {instance_data.get('DBInstanceIdentifier')}")
            cursor.close()
        except mysql.connector.Error as e:
            logger.error(f"❌ Error inserting data into database: {e}")
    
    def collect_rds_instances(self) -> List[Dict[str, Any]]:
        """Collect RDS instances from all specified regions."""
        logger.info(f"🔍 Starting RDS inventory collection across {len(self.regions)} regions")
        
        for region in self.regions:
            logger.info(f"📍 Scanning region: {region}")
            try:
                rds_client = self.session.client('rds', region_name=region)
                paginator = rds_client.get_paginator('describe_db_instances')
                
                for page in paginator.paginate():
                    for db_instance in page['DBInstances']:
                        instance_data = self._extract_instance_data(db_instance, region)
                        self.inventory_data.append(instance_data)
                        
                        # Insert into database if enabled
                        if self.store_in_db:
                            self._insert_into_database(instance_data)
                        
                        logger.debug(f"Found instance: {instance_data['DBInstanceIdentifier']}")
                        
            except ClientError as e:
                logger.error(f"❌ Error scanning region {region}: {e}")
            except Exception as e:
                logger.error(f"❌ Unexpected error in region {region}: {e}")
        
        logger.info(f"✅ Collection complete. Found {len(self.inventory_data)} RDS instances.")
        return self.inventory_data
    
    def _extract_instance_data(self, db_instance: Dict, region: str) -> Dict[str, Any]:
        """Extract relevant data from RDS instance description."""
        return {
            'aws_account_id': 'N/A',
            'Region': region,
            'DBInstanceIdentifier': db_instance.get('DBInstanceIdentifier', 'N/A'),
            'DBInstanceClass': db_instance.get('DBInstanceClass', 'N/A'),
            'Engine': db_instance.get('Engine', 'N/A'),
            'EngineVersion': db_instance.get('EngineVersion', 'N/A'),
            'DBInstanceStatus': db_instance.get('DBInstanceStatus', 'N/A'),
            'MasterUsername': db_instance.get('MasterUsername', 'N/A'),
            'Endpoint': db_instance.get('Endpoint', {}).get('Address', 'N/A') if db_instance.get('Endpoint') else 'N/A',
            'Port': db_instance.get('Endpoint', {}).get('Port', 'N/A') if db_instance.get('Endpoint') else 'N/A',
            'AllocatedStorage': db_instance.get('AllocatedStorage', 'N/A'),
            'StorageType': db_instance.get('StorageType', 'N/A'),
            'StorageEncrypted': db_instance.get('StorageEncrypted', False),
            'MultiAZ': db_instance.get('MultiAZ', False),
            'AvailabilityZone': db_instance.get('AvailabilityZone', 'N/A'),
            'VpcId': db_instance.get('DBSubnetGroup', {}).get('VpcId', 'N/A') if db_instance.get('DBSubnetGroup') else 'N/A',
            'PubliclyAccessible': db_instance.get('PubliclyAccessible', False),
            'BackupRetentionPeriod': db_instance.get('BackupRetentionPeriod', 'N/A'),
            'PreferredBackupWindow': db_instance.get('PreferredBackupWindow', 'N/A'),
            'PreferredMaintenanceWindow': db_instance.get('PreferredMaintenanceWindow', 'N/A'),
            'LatestRestorableTime': db_instance.get('LatestRestorableTime', 'N/A'),
            'InstanceCreateTime': db_instance.get('InstanceCreateTime', 'N/A'),
            'AutoMinorVersionUpgrade': db_instance.get('AutoMinorVersionUpgrade', False),
            'LicenseModel': db_instance.get('LicenseModel', 'N/A'),
            'DeletionProtection': db_instance.get('DeletionProtection', False),
            'IAMDatabaseAuthenticationEnabled': db_instance.get('IAMDatabaseAuthenticationEnabled', False),
            'PerformanceInsightsEnabled': db_instance.get('PerformanceInsightsEnabled', False),
        }
    
    def export_to_excel(self, filename: str = None):
        """Export collected inventory to Excel file."""
        if not self.inventory_data:
            logger.warning("No inventory data to export.")
            return
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"rds_inventory_{timestamp}.xlsx"
        
        logger.info(f"📊 Exporting inventory to {filename}")
        
        wb = Workbook()
        ws = wb.active
        ws.title = "RDS Inventory"
        
        # Define headers
        headers = list(self.inventory_data[0].keys())
        
        # Style for headers
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        # Write headers
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
        
        # Write data
        for row_num, instance in enumerate(self.inventory_data, 2):
            for col_num, header in enumerate(headers, 1):
                value = instance.get(header, 'N/A')
                # Convert datetime objects to strings
                if isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                ws.cell(row=row_num, column=col_num, value=value)
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Freeze the header row
        ws.freeze_panes = 'A2'
        
        wb.save(filename)
        logger.info(f"✅ Export complete: {filename}")
    
    def close_database(self):
        """Close database connection."""
        if self.db_connection and self.db_connection.is_connected():
            self.db_connection.close()
            logger.info("Database connection closed")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Collect AWS RDS inventory across multiple regions and export to Excel/Database'
    )
    parser.add_argument(
        '--profile',
        help='AWS profile name to use (default: default profile)',
        default=None
    )
    parser.add_argument(
        '--regions',
        nargs='+',
        help='Specific AWS regions to scan (default: all regions)',
        default=None
    )
    parser.add_argument(
        '--output',
        help='Output Excel filename (default: rds_inventory_TIMESTAMP.xlsx)',
        default=None
    )
    parser.add_argument(
        '--db',
        action='store_true',
        help='Store inventory in MySQL database (requires DB_* environment variables)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    try:
        collector = RDSInventoryCollector(
            profile=args.profile,
            regions=args.regions,
            store_in_db=args.db
        )
        collector.collect_rds_instances()
        
        # Export to Excel if not only storing in DB
        if not args.db or args.output:
            collector.export_to_excel(filename=args.output)
        
        collector.close_database()
        
    except NoCredentialsError:
        logger.error("❌ AWS credentials not found. Please configure your credentials.")
        return 1
    except Exception as e:
        logger.error(f"❌ An error occurred: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
