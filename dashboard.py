#!/usr/bin/env python3
"""
AWS RDS Inventory Dashboard - Simplified Version (No Pandas/NumPy)

Interactive Streamlit dashboard using pure Python for data handling.
No compilation issues on Windows!
"""

import streamlit as st
import mysql.connector
import os
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter, defaultdict

# Page configuration
st.set_page_config(
    page_title="AWS RDS Inventory Dashboard",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .bu-button {
        background-color: #f0f2f6;
        border: 2px solid #ddd;
        border-radius: 8px;
        padding: 12px 20px;
        margin: 5px;
        cursor: pointer;
        font-weight: 500;
        text-align: center;
        display: inline-block;
        transition: all 0.3s ease;
    }
    .bu-button:hover {
        background-color: #e0e6f2;
        border-color: #4472ca;
    }
    .bu-button.active {
        background-color: #4472ca;
        color: white;
        border-color: #4472ca;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state for BU filter
if 'selected_bu' not in st.session_state:
    st.session_state.selected_bu = None


def load_env_file(env_path: str = '.env'):
    """Load environment variables from .env file."""
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()


@st.cache_resource
def get_db_connection():
    """Establish database connection (cached)."""
    load_env_file('.env')
    
    db_host = os.getenv('DB_HOST')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_name = os.getenv('DB_NAME')
    
    if not all([db_host, db_user, db_password, db_name]):
        st.error("❌ Database credentials not found. Please check .env file.")
        st.stop()
    
    try:
        connection = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            autocommit=True,
            connection_timeout=30
        )
        return connection
    except mysql.connector.Error as e:
        st.error(f"❌ Failed to connect to database: {e}")
        st.stop()


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_rds_inventory():
    """Load RDS inventory from database as list of dictionaries."""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    query = "SELECT * FROM rds_inventory ORDER BY collection_timestamp DESC"
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    
    return data


def get_summary_stats(data):
    """Calculate summary statistics from raw data."""
    if not data:
        return {}
    
    total_storage = sum(int(row.get('allocated_storage', 0)) for row in data if row.get('allocated_storage', 0))
    multi_az = sum(1 for row in data if row.get('multi_az') == True or row.get('multi_az') == 1)
    publicly_accessible = sum(1 for row in data if row.get('publicly_accessible') == True or row.get('publicly_accessible') == 1)
    
    bu_names = [row.get('bu_name') for row in data]
    regions = [row.get('region') for row in data]
    engines = [row.get('engine') for row in data]
    
    return {
        'total_instances': len(data),
        'total_storage': total_storage,
        'multi_az': multi_az,
        'publicly_accessible': publicly_accessible,
        'unique_bus': len(set(bu_names)),
        'unique_regions': len(set(regions)),
        'unique_engines': len(set(engines)),
    }


def create_simple_dataframe(data, columns):
    """Convert list of dicts to simple table format for display."""
    return data


def main():
    """Main dashboard application."""
    
    # Sidebar
    st.sidebar.title("🗄️ RDS Inventory Dashboard")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Select Page:",
        ["📊 Overview", "🔍 Instance Browser", "📈 Analytics", "ℹ️ About"]
    )
    
    # Load data
    try:
        data = load_rds_inventory()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return
    
    if page == "📊 Overview":
        overview_page(data)
    elif page == "🔍 Instance Browser":
        browser_page(data)
    elif page == "📈 Analytics":
        analytics_page(data)
    elif page == "ℹ️ About":
        about_page(data)


def overview_page(data):
    """Overview/Home page with key metrics and charts."""
    st.title("📊 RDS Inventory Overview")
    
    # Get summary stats
    stats = get_summary_stats(data)
    
    # Last updated info
    if data:
        last_updated = data[0].get('collection_timestamp')
        st.info(f"📅 Last Updated: {last_updated}")
    
    # Key Metrics
    st.markdown("### 📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Instances", stats.get('total_instances', 0), "RDS DBs")
    with col2:
        st.metric("Business Units", stats.get('unique_bus', 0), "Teams")
    with col3:
        st.metric("Regions", stats.get('unique_regions', 0), "AWS Regions")
    with col4:
        st.metric("Engine Types", stats.get('unique_engines', 0), "Database Engines")
    
    # Storage Summary
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Storage", f"{stats.get('total_storage', 0):,} GB", "Allocated")
    with col2:
        multi_az_pct = (stats.get('multi_az', 0) / stats.get('total_instances', 1) * 100) if stats.get('total_instances', 0) > 0 else 0
        st.metric("Multi-AZ Instances", stats.get('multi_az', 0), 
                  f"{multi_az_pct:.1f}%")
    
    st.markdown("---")
    
    # Business Unit Filter Buttons
    st.markdown("### 🎯 Filter by Business Unit")
    
    bu_list = sorted(list(set(row.get('bu_name') for row in data)))
    
    # Create columns for BU buttons
    cols = st.columns(len(bu_list))
    for idx, bu in enumerate(bu_list):
        with cols[idx]:
            if st.button(bu, key=f"bu_btn_{bu}", use_container_width=True):
                st.session_state.selected_bu = bu
                st.rerun()
    
    # Show selected BU or all data
    if st.session_state.selected_bu:
        filtered_data = [row for row in data if row.get('bu_name') == st.session_state.selected_bu]
        col1, col2 = st.columns([4, 1])
        with col1:
            st.success(f"📍 Filtered by: **{st.session_state.selected_bu}**")
        with col2:
            if st.button("❌ Clear Filter", use_container_width=True):
                st.session_state.selected_bu = None
                st.rerun()
    else:
        filtered_data = data
    
    st.markdown("---")
    
    # Charts - Row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Instances by Business Unit")
        bu_counts = Counter(row.get('bu_name') for row in filtered_data)
        bu_df_dict = {
            'Business Unit': list(bu_counts.keys()),
            'Count': list(bu_counts.values())
        }
        fig = px.pie(bu_df_dict, values='Count', names='Business Unit',
                    title="RDS Distribution by BU")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Instances by Region")
        region_counts = Counter(row.get('region') for row in filtered_data)
        region_list = sorted(region_counts.items(), key=lambda x: x[1], reverse=True)
        region_df_dict = {
            'Region': [x[0] for x in region_list],
            'Count': [x[1] for x in region_list]
        }
        fig = px.bar(region_df_dict, x='Region', y='Count',
                    title="RDS Distribution by Region",
                    labels={'Count': 'Number of Instances'})
        st.plotly_chart(fig, use_container_width=True)
    
    # Charts - Row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Instances by Engine Type")
        engine_counts = Counter(row.get('engine') for row in filtered_data)
        engine_list = sorted(engine_counts.items(), key=lambda x: x[1], reverse=True)
        engine_df_dict = {
            'Engine': [x[0] for x in engine_list],
            'Count': [x[1] for x in engine_list]
        }
        fig = px.bar(engine_df_dict, x='Engine', y='Count',
                    title="RDS Distribution by Engine",
                    labels={'Count': 'Number of Instances'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Multi-AZ vs Single-AZ")
        multi_az_count = sum(1 for row in filtered_data if row.get('multi_az') == True or row.get('multi_az') == 1)
        single_az_count = len(filtered_data) - multi_az_count
        multi_az_data = {
            'Type': ['Multi-AZ', 'Single-AZ'],
            'Count': [multi_az_count, single_az_count]
        }
        fig = px.pie(multi_az_data, values='Count', names='Type',
                    title="High Availability Distribution")
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Instance Status
    st.markdown("### Instance Status Distribution")
    status_counts = Counter(row.get('db_instance_status') for row in filtered_data)
    status_list = sorted(status_counts.items(), key=lambda x: x[1], reverse=True)
    status_df_dict = {
        'Status': [x[0] for x in status_list],
        'Count': [x[1] for x in status_list]
    }
    fig = px.bar(status_df_dict, x='Status', y='Count',
                title="RDS Instance Status",
                labels={'Count': 'Number of Instances'},
                color='Status')
    st.plotly_chart(fig, use_container_width=True)


def browser_page(data):
    """Instance browser page with filters and search."""
    st.title("🔍 Instance Browser")
    
    st.markdown("### 🔎 Search & Filter")
    
    # Get unique values for filters
    bu_list = sorted(list(set(row.get('bu_name') for row in data)))
    region_list = sorted(list(set(row.get('region') for row in data)))
    engine_list = sorted(list(set(row.get('engine') for row in data)))
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        search_term = st.text_input("Search by Instance Name", "")
    
    with col2:
        bu_filter = st.multiselect(
            "Filter by Business Unit",
            bu_list,
            default=bu_list
        )
    
    with col3:
        region_filter = st.multiselect(
            "Filter by Region",
            region_list,
            default=region_list
        )
    
    with col4:
        engine_filter = st.multiselect(
            "Filter by Engine",
            engine_list,
            default=engine_list
        )
    
    # Apply filters
    filtered_data = data.copy()
    
    if search_term:
        filtered_data = [row for row in filtered_data 
                        if search_term.lower() in row.get('db_instance_identifier', '').lower()]
    
    filtered_data = [row for row in filtered_data 
                    if row.get('bu_name') in bu_filter and
                       row.get('region') in region_filter and
                       row.get('engine') in engine_filter]
    
    st.markdown("---")
    
    # Results summary
    total_storage = sum(int(row.get('allocated_storage', 0)) for row in filtered_data if row.get('allocated_storage', 0))
    multi_az_count = sum(1 for row in filtered_data if row.get('multi_az') == True or row.get('multi_az') == 1)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Filtered Results", len(filtered_data), "instances")
    with col2:
        st.metric("Total Storage", f"{total_storage:,} GB")
    with col3:
        st.metric("Multi-AZ", multi_az_count)
    
    st.markdown("---")
    
    # Display table
    st.markdown("### 📋 RDS Instances")
    
    if filtered_data:
        # Create table for display
        display_columns = [
            'bu_name', 'db_instance_identifier', 'engine', 'engine_version',
            'db_instance_class', 'allocated_storage', 'storage_type', 'region',
            'multi_az', 'db_instance_status', 'publicly_accessible', 'endpoint_address'
        ]
        
        # Create list of lists for display
        table_data = []
        for row in filtered_data:
            table_data.append([
                row.get('bu_name', 'N/A'),
                row.get('db_instance_identifier', 'N/A'),
                row.get('engine', 'N/A'),
                row.get('engine_version', 'N/A'),
                row.get('db_instance_class', 'N/A'),
                row.get('allocated_storage', 'N/A'),
                row.get('storage_type', 'N/A'),
                row.get('region', 'N/A'),
                row.get('multi_az', 'N/A'),
                row.get('db_instance_status', 'N/A'),
                row.get('publicly_accessible', 'N/A'),
                row.get('endpoint_address', 'N/A'),
            ])
        
        # Display as dataframe-like table
        st.dataframe(
            {
                'BU': [r[0] for r in table_data],
                'Instance Name': [r[1] for r in table_data],
                'Engine': [r[2] for r in table_data],
                'Version': [r[3] for r in table_data],
                'Instance Class': [r[4] for r in table_data],
                'Storage (GB)': [r[5] for r in table_data],
                'Storage Type': [r[6] for r in table_data],
                'Region': [r[7] for r in table_data],
                'Multi-AZ': [r[8] for r in table_data],
                'Status': [r[9] for r in table_data],
                'Public': [r[10] for r in table_data],
                'Endpoint': [r[11] for r in table_data],
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("No instances found matching your filters.")
    
    # Export option
    st.markdown("---")
    if st.button("📥 Export Filtered Data as CSV"):
        if filtered_data:
            csv_content = "bu_name,db_instance_identifier,engine,engine_version,db_instance_class,allocated_storage,storage_type,region,multi_az,db_instance_status,publicly_accessible,endpoint_address\n"
            for row in filtered_data:
                csv_content += f"{row.get('bu_name','')},{row.get('db_instance_identifier','')},{row.get('engine','')},{row.get('engine_version','')},{row.get('db_instance_class','')},{row.get('allocated_storage','')},{row.get('storage_type','')},{row.get('region','')},{row.get('multi_az','')},{row.get('db_instance_status','')},{row.get('publicly_accessible','')},{row.get('endpoint_address','')}\n"
            
            st.download_button(
                label="Download CSV",
                data=csv_content,
                file_name=f"rds_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )


def analytics_page(data):
    """Analytics page with detailed insights."""
    st.title("📈 Analytics & Insights")
    
    st.markdown("### 💾 Storage Analysis")
    
    # Storage by BU
    col1, col2 = st.columns(2)
    
    with col1:
        bu_storage = defaultdict(int)
        for row in data:
            bu = row.get('bu_name')
            storage = int(row.get('allocated_storage', 0))
            bu_storage[bu] += storage
        
        storage_by_bu = sorted(bu_storage.items(), key=lambda x: x[1], reverse=True)
        storage_df = {
            'Business Unit': [x[0] for x in storage_by_bu],
            'Storage (GB)': [x[1] for x in storage_by_bu]
        }
        fig = px.bar(storage_df, x='Business Unit', y='Storage (GB)',
                    title="Total Storage by Business Unit",
                    labels={'Storage (GB)': 'Allocated Storage (GB)'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        region_storage = defaultdict(int)
        for row in data:
            region = row.get('region')
            storage = int(row.get('allocated_storage', 0))
            region_storage[region] += storage
        
        storage_by_region = sorted(region_storage.items(), key=lambda x: x[1], reverse=True)
        storage_df = {
            'Region': [x[0] for x in storage_by_region],
            'Storage (GB)': [x[1] for x in storage_by_region]
        }
        fig = px.bar(storage_df, x='Region', y='Storage (GB)',
                    title="Total Storage by Region",
                    labels={'Storage (GB)': 'Allocated Storage (GB)'})
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 🔐 Security Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Publicly accessible instances
        public_instances = [row for row in data if row.get('publicly_accessible') == True or row.get('publicly_accessible') == 1]
        st.warning(f"⚠️ Publicly Accessible Instances: {len(public_instances)}")
        
        if public_instances:
            public_display = {
                'BU': [row.get('bu_name', 'N/A') for row in public_instances],
                'Instance': [row.get('db_instance_identifier', 'N/A') for row in public_instances],
                'Region': [row.get('region', 'N/A') for row in public_instances],
                'Engine': [row.get('engine', 'N/A') for row in public_instances],
            }
            st.dataframe(public_display, use_container_width=True, hide_index=True)
    
    with col2:
        # Backup retention
        backups = [int(row.get('backup_retention_period', 0)) for row in data if row.get('backup_retention_period', 0)]
        avg_backup = sum(backups) / len(backups) if backups else 0
        st.info(f"📅 Average Backup Retention: {avg_backup:.1f} days")
        
        retention_counter = Counter(row.get('backup_retention_period') for row in data if row.get('backup_retention_period'))
        retention_list = sorted(retention_counter.items())
        retention_df = {
            'Days': [str(x[0]) for x in retention_list],
            'Count': [x[1] for x in retention_list]
        }
        fig = px.bar(retention_df, x='Days', y='Count',
                    title="Backup Retention Distribution",
                    labels={'Count': 'Number of Instances'})
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 📊 Instance Class Analysis")
    
    instance_class_counter = Counter(row.get('db_instance_class') for row in data)
    instance_class_list = instance_class_counter.most_common(10)
    instance_df = {
        'Instance Class': [x[0] for x in instance_class_list],
        'Count': [x[1] for x in instance_class_list]
    }
    fig = px.bar(instance_df, x='Instance Class', y='Count',
                title="Top 10 Instance Classes",
                labels={'Count': 'Number of Instances'})
    st.plotly_chart(fig, use_container_width=True)


def about_page(data):
    """About page with information."""
    st.title("ℹ️ About")
    
    st.markdown("""
    ## AWS RDS Inventory Dashboard
    
    A comprehensive dashboard for managing and monitoring RDS database instances across multiple AWS accounts and regions.
    
    ### Features
    - 📊 **Overview Dashboard** - Key metrics and visualizations
    - 🔍 **Instance Browser** - Search, filter, and explore RDS instances
    - 📈 **Analytics** - Detailed insights and analysis
    - 💾 **Data Export** - Download filtered data as CSV
    - 🎯 **Business Unit Filtering** - Quick filter by BU buttons
    
    ### Data Information
    """)
    
    try:
        stats = get_summary_stats(data)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Instances", stats.get('total_instances', 0))
        with col2:
            if data:
                last_updated = data[0].get('collection_timestamp')
                st.metric("Last Updated", str(last_updated)[:19])
            else:
                st.metric("Last Updated", "N/A")
        with col3:
            st.metric("Total Business Units", stats.get('unique_bus', 0))
        
        st.markdown("---")
        st.markdown("### Database Schema")
        st.write("The dashboard pulls data from the following columns:")
        
        columns_info = {
            'aws_account_id': 'AWS Account ID',
            'bu_name': 'Business Unit Name (Profile)',
            'region': 'AWS Region',
            'db_instance_identifier': 'RDS Instance Name',
            'db_instance_class': 'Instance Type',
            'engine': 'Database Engine (MySQL, PostgreSQL, etc)',
            'engine_version': 'Engine Version',
            'db_instance_status': 'Current Status',
            'allocated_storage': 'Storage in GB',
            'storage_type': 'Storage Type (gp2, io1, etc)',
            'multi_az': 'Multi-AZ Enabled',
            'backup_retention_period': 'Backup Retention Days',
            'endpoint_address': 'Connection Endpoint',
        }
        
        schema_display = {
            'Column': list(columns_info.keys()),
            'Description': list(columns_info.values())
        }
        st.dataframe(schema_display, use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
    
    st.markdown("---")
    st.markdown("""
    ### Support
    For issues or feature requests, please contact your DevOps team.
    
    ### Dashboard Version
    Version 1.2.0 (Windows Compatible - Business Unit Filter Buttons)
    """)


if __name__ == "__main__":
    main()
