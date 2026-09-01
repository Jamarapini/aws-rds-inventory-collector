#!/usr/bin/env python3
"""
AWS RDS Inventory Collector

Collects RDS instance information across multiple AWS regions and accounts,
and exports the data to Excel format.
"""

import boto3
import argparse
import logging
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
    
    def __init__(self, profile: str = None, regions: List[str] = None):
        """
        Initialize the RDS Inventory Collector.
        
        Args:
            profile: AWS profile name to use
            regions: List of AWS regions to scan. If None, scans all available regions.
        """
        self.profile = profile
        self.session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        self.regions = regions or self._get_all_regions()
        self.inventory_data = []
        
    def _get_all_regions(self) -> List[str]:
        """Get all available AWS regions for RDS."""
        try:
            ec2_client = self.session.client('ec2', region_name='us-east-1')
            regions = ec2_client.describe_regions()
            return [region['RegionName'] for region in regions['Regions']]
        except Exception as e:
            logger.warning(f"Could not retrieve all regions: {e}. Using default regions.")
            return ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1']
    
    def collect_rds_instances(self) -> List[Dict[str, Any]]:
        """Collect RDS instances from all specified regions."""
        logger.info(f"Starting RDS inventory collection across {len(self.regions)} regions")
        
        for region in self.regions:
            logger.info(f"Scanning region: {region}")
            try:
                rds_client = self.session.client('rds', region_name=region)
                paginator = rds_client.get_paginator('describe_db_instances')
                
                for page in paginator.paginate():
                    for db_instance in page['DBInstances']:
                        instance_data = self._extract_instance_data(db_instance, region)
                        self.inventory_data.append(instance_data)
                        logger.debug(f"Found instance: {instance_data['DBInstanceIdentifier']}")
                        
            except ClientError as e:
                logger.error(f"Error scanning region {region}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error in region {region}: {e}")
        
        logger.info(f"Collection complete. Found {len(self.inventory_data)} RDS instances.")
        return self.inventory_data
    
    def _extract_instance_data(self, db_instance: Dict, region: str) -> Dict[str, Any]:
        """Extract relevant data from RDS instance description."""
        return {
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
        
        logger.info(f"Exporting inventory to {filename}")
        
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
        logger.info(f"Export complete: {filename}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Collect AWS RDS inventory across multiple regions and export to Excel'
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
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    try:
        collector = RDSInventoryCollector(profile=args.profile, regions=args.regions)
        collector.collect_rds_instances()
        collector.export_to_excel(filename=args.output)
        
    except NoCredentialsError:
        logger.error("AWS credentials not found. Please configure your credentials.")
        return 1
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
