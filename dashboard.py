#!/usr/bin/env python3
"""
AWS RDS Inventory Dashboard

Interactive Streamlit dashboard to visualize and manage RDS inventory data
stored in MySQL database.
"""

import streamlit as st
import pandas as pd
import mysql.connector
import os
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

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
    </style>
    """, unsafe_allow_html=True)


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
    """Load RDS inventory from database."""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    query = "SELECT * FROM rds_inventory ORDER BY collection_timestamp DESC"
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    
    return pd.DataFrame(data)


def parse_tags(tags_json):
    """Parse JSON tags string to dictionary."""
    try:
        if tags_json == 'N/A' or pd.isna(tags_json):
            return {}
        return json.loads(tags_json)
    except:
        return {}


def get_summary_stats(df):
    """Calculate summary statistics."""
    return {
        'total_instances': len(df),
        'total_storage': df['allocated_storage'].sum(),
        'multi_az': len(df[df['multi_az'] == True]),
        'publicly_accessible': len(df[df['publicly_accessible'] == True]),
        'unique_bus': df['bu_name'].nunique(),
        'unique_regions': df['region'].nunique(),
        'unique_engines': df['engine'].nunique(),
    }


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
        df = load_rds_inventory()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return
    
    if page == "📊 Overview":
        overview_page(df)
    elif page == "🔍 Instance Browser":
        browser_page(df)
    elif page == "📈 Analytics":
        analytics_page(df)
    elif page == "ℹ️ About":
        about_page()


def overview_page(df):
    """Overview/Home page with key metrics and charts."""
    st.title("📊 RDS Inventory Overview")
    
    # Get summary stats
    stats = get_summary_stats(df)
    
    # Last updated info
    if not df.empty:
        last_updated = df['collection_timestamp'].max()
        st.info(f"📅 Last Updated: {last_updated}")
    
    # Key Metrics
    st.markdown("### 📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Instances", stats['total_instances'], "RDS DBs")
    with col2:
        st.metric("Business Units", stats['unique_bus'], "Teams")
    with col3:
        st.metric("Regions", stats['unique_regions'], "AWS Regions")
    with col4:
        st.metric("Engine Types", stats['unique_engines'], "Database Engines")
    
    # Storage Summary
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Storage", f"{stats['total_storage']:,} GB", "Allocated")
    with col2:
        st.metric("Multi-AZ Instances", stats['multi_az'], 
                  f"{(stats['multi_az']/stats['total_instances']*100):.1f}%")
    
    st.markdown("---")
    
    # Charts - Row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Instances by Business Unit")
        bu_counts = df['bu_name'].value_counts().reset_index()
        bu_counts.columns = ['Business Unit', 'Count']
        fig = px.pie(bu_counts, values='Count', names='Business Unit',
                    title="RDS Distribution by BU")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Instances by Region")
        region_counts = df['region'].value_counts().reset_index()
        region_counts.columns = ['Region', 'Count']
        fig = px.bar(region_counts, x='Region', y='Count',
                    title="RDS Distribution by Region",
                    labels={'Count': 'Number of Instances'})
        st.plotly_chart(fig, use_container_width=True)
    
    # Charts - Row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Instances by Engine Type")
        engine_counts = df['engine'].value_counts().reset_index()
        engine_counts.columns = ['Engine', 'Count']
        fig = px.bar(engine_counts, x='Engine', y='Count',
                    title="RDS Distribution by Engine",
                    labels={'Count': 'Number of Instances'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Multi-AZ vs Single-AZ")
        multi_az_data = pd.DataFrame({
            'Type': ['Multi-AZ', 'Single-AZ'],
            'Count': [stats['multi_az'], stats['total_instances'] - stats['multi_az']]
        })
        fig = px.pie(multi_az_data, values='Count', names='Type',
                    title="High Availability Distribution")
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Instance Status
    st.markdown("### Instance Status Distribution")
    status_counts = df['db_instance_status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    fig = px.bar(status_counts, x='Status', y='Count',
                title="RDS Instance Status",
                labels={'Count': 'Number of Instances'},
                color='Status')
    st.plotly_chart(fig, use_container_width=True)


def browser_page(df):
    """Instance browser page with filters and search."""
    st.title("🔍 Instance Browser")
    
    st.markdown("### 🔎 Search & Filter")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        search_term = st.text_input("Search by Instance Name", "")
    
    with col2:
        bu_filter = st.multiselect(
            "Filter by Business Unit",
            sorted(df['bu_name'].unique()),
            default=sorted(df['bu_name'].unique())
        )
    
    with col3:
        region_filter = st.multiselect(
            "Filter by Region",
            sorted(df['region'].unique()),
            default=sorted(df['region'].unique())
        )
    
    with col4:
        engine_filter = st.multiselect(
            "Filter by Engine",
            sorted(df['engine'].unique()),
            default=sorted(df['engine'].unique())
        )
    
    # Apply filters
    filtered_df = df.copy()
    
    if search_term:
        filtered_df = filtered_df[
            filtered_df['db_instance_identifier'].str.contains(search_term, case=False, na=False)
        ]
    
    filtered_df = filtered_df[
        (filtered_df['bu_name'].isin(bu_filter)) &
        (filtered_df['region'].isin(region_filter)) &
        (filtered_df['engine'].isin(engine_filter))
    ]
    
    st.markdown("---")
    
    # Results summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Filtered Results", len(filtered_df), "instances")
    with col2:
        st.metric("Total Storage", f"{filtered_df['allocated_storage'].sum():,} GB")
    with col3:
        st.metric("Multi-AZ", len(filtered_df[filtered_df['multi_az'] == True]))
    
    st.markdown("---")
    
    # Display table
    st.markdown("### 📋 RDS Instances")
    
    # Select columns to display
    display_columns = [
        'bu_name', 'db_instance_identifier', 'engine', 'engine_version',
        'db_instance_class', 'allocated_storage', 'storage_type', 'region',
        'multi_az', 'db_instance_status', 'publicly_accessible', 'endpoint_address'
    ]
    
    display_df = filtered_df[display_columns].copy()
    display_df = display_df.rename(columns={
        'bu_name': 'BU',
        'db_instance_identifier': 'Instance Name',
        'engine': 'Engine',
        'engine_version': 'Version',
        'db_instance_class': 'Instance Class',
        'allocated_storage': 'Storage (GB)',
        'storage_type': 'Storage Type',
        'region': 'Region',
        'multi_az': 'Multi-AZ',
        'db_instance_status': 'Status',
        'publicly_accessible': 'Public',
        'endpoint_address': 'Endpoint'
    })
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Export option
    st.markdown("---")
    if st.button("📥 Export Filtered Data as CSV"):
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"rds_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )


def analytics_page(df):
    """Analytics page with detailed insights."""
    st.title("📈 Analytics & Insights")
    
    st.markdown("### 💾 Storage Analysis")
    
    # Storage by BU
    col1, col2 = st.columns(2)
    
    with col1:
        storage_by_bu = df.groupby('bu_name')['allocated_storage'].sum().sort_values(ascending=False).reset_index()
        storage_by_bu.columns = ['Business Unit', 'Storage (GB)']
        fig = px.bar(storage_by_bu, x='Business Unit', y='Storage (GB)',
                    title="Total Storage by Business Unit",
                    labels={'Storage (GB)': 'Allocated Storage (GB)'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        storage_by_region = df.groupby('region')['allocated_storage'].sum().sort_values(ascending=False).reset_index()
        storage_by_region.columns = ['Region', 'Storage (GB)']
        fig = px.bar(storage_by_region, x='Region', y='Storage (GB)',
                    title="Total Storage by Region",
                    labels={'Storage (GB)': 'Allocated Storage (GB)'})
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 🔐 Security Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Publicly accessible instances
        public_instances = df[df['publicly_accessible'] == True]
        st.warning(f"⚠️ Publicly Accessible Instances: {len(public_instances)}")
        
        if len(public_instances) > 0:
            st.dataframe(
                public_instances[['bu_name', 'db_instance_identifier', 'region', 'engine']],
                use_container_width=True,
                hide_index=True
            )
    
    with col2:
        # Backup retention
        st.info(f"📅 Average Backup Retention: {df['backup_retention_period'].mean():.1f} days")
        
        retention_dist = df.groupby('backup_retention_period').size().reset_index(name='Count')
        fig = px.bar(retention_dist, x='backup_retention_period', y='Count',
                    title="Backup Retention Distribution",
                    labels={'backup_retention_period': 'Days', 'Count': 'Number of Instances'})
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 📊 Instance Class Analysis")
    
    instance_class_dist = df['db_instance_class'].value_counts().head(10).reset_index()
    instance_class_dist.columns = ['Instance Class', 'Count']
    fig = px.bar(instance_class_dist, x='Instance Class', y='Count',
                title="Top 10 Instance Classes",
                labels={'Count': 'Number of Instances'})
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 🗺️ Region × BU Matrix")
    
    # Create heatmap data
    heatmap_data = pd.crosstab(df['region'], df['bu_name'])
    fig = go.Figure(data=go.Heatmap(z=heatmap_data.values,
                                     x=heatmap_data.columns,
                                     y=heatmap_data.index,
                                     colorscale='Blues'))
    fig.update_layout(title="RDS Instances Distribution: Region × Business Unit",
                     xaxis_title="Business Unit",
                     yaxis_title="Region")
    st.plotly_chart(fig, use_container_width=True)


def about_page():
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
    
    ### Data Information
    """)
    
    try:
        df = load_rds_inventory()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Instances", len(df))
        with col2:
            last_updated = df['collection_timestamp'].max()
            st.metric("Last Updated", last_updated.strftime('%Y-%m-%d %H:%M:%S'))
        with col3:
            st.metric("Total Business Units", df['bu_name'].nunique())
        
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
        
        schema_df = pd.DataFrame(list(columns_info.items()), columns=['Column', 'Description'])
        st.dataframe(schema_df, use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
    
    st.markdown("---")
    st.markdown("""
    ### Support
    For issues or feature requests, please contact your DevOps team.
    
    ### Dashboard Version
    Version 1.0.0
    """)


if __name__ == "__main__":
    main()
