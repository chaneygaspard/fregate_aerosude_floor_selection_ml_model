#!/usr/bin/env python3
"""
Extended ML Training Data Visualization Script
Generates comprehensive visualizations of RTLS positioning data from ml_training_data_exte_new/
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, List, Tuple
import glob
from datetime import datetime

# Set style for better-looking plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Configuration
DATA_DIR = "ml_training_data_exte_new"
OUTPUT_DIR = "visualizations_exte"

# Tag MAC to floor mapping (from floor_success_rate.py)
TAG_MAC_TO_FLOOR = {
    # Downstairs tags (floor = 0)
    'f260a59af3be': 0, 'e45428cd811f': 0, 'eaf519e486b7': 0, 'e71ebc086c12': 0,
    'db87600e1088': 0, 'e75675d44213': 0, 'ea0efa76b1d7': 0, 'e3c858bb535e': 0,
    'f9cf5a96910d': 0, 'e9ee05861174': 0, 'c5d89d98d531': 0, 'f17508753dd2': 0,
    'ccd6b409ba05': 0, 'cfcba5a4aa8c': 0, 'dfe232164c0a': 0, 'ea130331a7d6': 0,
    'fe916ad112d4': 0, 'cbafa76ff612': 0, 'd31e40a36148': 0, 'ed3dc76b5057': 0,
    'f7fb6d248542': 0, 'e5618db03315': 0, 'c48718b206de': 0, 'ced95ba5af64': 0,
    'e80511ee6f95': 0, 'f8e68ad462b8': 0, 'c07f2aebbfb2': 0, 'dc6fd1014985': 0,
    'dbdfe63c5bfe': 0, 'f53d908ae87e': 0,
    
    # Mezzanine/upstairs tags (floor = 1)
    'eacbbb80d2ae': 1, 'd55a17359cec': 1, 'c3fdcfc7cde7': 1, 'dd35e8065e41': 1,
    'f1465d4b34ad': 1, 'd2433d346da0': 1, 'de8a7eb407c5': 1, 'fbde6b71de2c': 1,
    'eed4934cb925': 1, 'c694e5297d8c': 1, 'dcb814adee27': 1, 'ee1ae8c0199b': 1,
    'e12a0889fc9d': 1, 'ca70faad5185': 1, 'e1221fc96df8': 1, 'eabf49388a88': 1,
    'faebae16f304': 1, 'e6a1121bd9ba': 1, 'ebc3d8c27268': 1, 'c0c28a5250d1': 1,
    'eb7dd4251a0b': 1, 'dbd8f214e90c': 1, 'f8c6e10eb94d': 1, 'c61444ecfa21': 1,
    'e6dee509ceb7': 1, 'e0187539099c': 1, 'cfa33b8f966f': 1, 'd1162b91f43c': 1,
    'd908a64ff5c8': 1, 'e0179d3286a1': 1
}

def create_output_dir():
    """Create output directory for visualizations"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"📁 Created output directory: {OUTPUT_DIR}/")

def get_file_stats() -> pd.DataFrame:
    """Get basic statistics about all CSV files"""
    files_info = []
    csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    
    for file_path in csv_files:
        filename = os.path.basename(file_path)
        tag_mac = filename.replace('.csv', '')
        
        # Get file size
        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)
        
        # Count lines (approximate message count)
        try:
            with open(file_path, 'r') as f:
                line_count = sum(1 for _ in f) - 1  # Subtract header
        except:
            line_count = 0
        
        # Get floor info
        floor = TAG_MAC_TO_FLOOR.get(tag_mac, -1)
        floor_name = "Downstairs" if floor == 0 else "Mezzanine" if floor == 1 else "Unknown"
        
        files_info.append({
            'tag_mac': tag_mac,
            'filename': filename,
            'size_mb': size_mb,
            'message_count': line_count,
            'floor': floor,
            'floor_name': floor_name
        })
    
    return pd.DataFrame(files_info)

def plot_message_distribution(df: pd.DataFrame):
    """Plot message count distribution across tags"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Bar plot of message counts
    df_sorted = df.sort_values('message_count', ascending=False)
    bars = ax1.bar(range(len(df_sorted)), df_sorted['message_count'], 
                   color=['orange' if floor == 0 else 'skyblue' for floor in df_sorted['floor']])
    ax1.set_title('Extended Data: Messages per Tag (Sorted)', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Tag Index')
    ax1.set_ylabel('Message Count')
    ax1.grid(True, alpha=0.3)
    
    # Add legend for colors
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='orange', label='Downstairs'),
                      Patch(facecolor='skyblue', label='Mezzanine')]
    ax1.legend(handles=legend_elements)
    
    # Histogram of message counts
    ax2.hist(df['message_count'], bins=20, alpha=0.7, color='green', edgecolor='black')
    ax2.set_title('Extended Data: Distribution of Message Counts', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Message Count')
    ax2.set_ylabel('Number of Tags')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/message_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_spatial_distribution(df: pd.DataFrame):
    """Plot spatial distribution of tags overlaid on floor plan"""
    # Floor vertices from plotter.py (X, Y coordinates only)
    floor_verts = np.array([
        [12.0, 45.6], 
        [12.0, 40.1], 
        [22.5, 40.1], 
        [22.5, 36.3], 
        [52.7, 36.3], 
        [52.7, 37.3], 
        [66.6, 37.3], 
        [66.6, 45.6],
        [12.0, 45.6]  # Close the polygon
    ])
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
    
    # Collect positioning data for each floor
    downstairs_positions = []
    mezzanine_positions = []
    
    # Use ALL 60 tags for comprehensive coverage
    print("  📊 Reading positioning data from all 60 tags (Extended Data)...")
    
    for _, row in df.iterrows():
        filename = row['filename']
        tag_mac = row['tag_mac']
        floor = row['floor']
        
        file_path = os.path.join(DATA_DIR, filename)
        
        try:
            # Read positioning data including true_map_id for floor determination
            sample_data = pd.read_csv(file_path, usecols=['tag_x', 'tag_y', 'true_map_id'])
            
            # Take every 5th row to get good coverage while keeping it manageable
            if len(sample_data) > 50:
                sample_data = sample_data.iloc[::5]  # Every 5th row instead of 10th
            
            # Use true_map_id to determine actual floor
            for _, pos_row in sample_data.iterrows():
                x, y, true_map = pos_row['tag_x'], pos_row['tag_y'], pos_row['true_map_id']
                
                if true_map == '682c66de8cde618ce1270230':  # Downstairs
                    downstairs_positions.append([x, y])
                elif true_map == '682c66f08cde618ce127025e':  # Mezzanine
                    mezzanine_positions.append([x, y])
                
        except Exception as e:
            print(f"Could not read positioning data from {filename}: {e}")
    
    print(f"  📈 Loaded extended data from {len(df)} tags total")
    
    # Plot downstairs
    ax1.plot(floor_verts[:, 0], floor_verts[:, 1], 'k-', linewidth=3, label='Floor Plan')
    ax1.fill(floor_verts[:, 0], floor_verts[:, 1], alpha=0.1, color='gray')
    
    if downstairs_positions:
        downstairs_positions = np.array(downstairs_positions)
        ax1.scatter(downstairs_positions[:, 0], downstairs_positions[:, 1], 
                   alpha=0.4, s=1, color='orange', label='Tag Positions')
        
    ax1.set_title('Extended Data - Downstairs: Spatial Distribution', fontsize=14, fontweight='bold')
    ax1.set_xlabel('X Position (meters)')
    ax1.set_ylabel('Y Position (meters)')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    ax1.set_aspect('equal')
    ax1.invert_yaxis()  # Flip y-axis to match proper orientation
    
    # Plot mezzanine
    ax2.plot(floor_verts[:, 0], floor_verts[:, 1], 'k-', linewidth=3, label='Floor Plan')
    ax2.fill(floor_verts[:, 0], floor_verts[:, 1], alpha=0.1, color='gray')
    
    if mezzanine_positions:
        mezzanine_positions = np.array(mezzanine_positions)
        ax2.scatter(mezzanine_positions[:, 0], mezzanine_positions[:, 1], 
                   alpha=0.4, s=1, color='skyblue', label='Tag Positions')
        
    ax2.set_title('Extended Data - Mezzanine: Spatial Distribution', fontsize=14, fontweight='bold')
    ax2.set_xlabel('X Position (meters)')
    ax2.set_ylabel('Y Position (meters)')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    ax2.set_aspect('equal')
    ax2.invert_yaxis()  # Flip y-axis to match proper orientation
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/spatial_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  📍 Plotted {len(downstairs_positions)} downstairs positions and {len(mezzanine_positions)} mezzanine positions")

def plot_correct_positions(df: pd.DataFrame):
    """Plot only positions where computed map_id matches true_map_id (correct positioning)"""
    # Floor vertices from plotter.py (X, Y coordinates only)
    floor_verts = np.array([
        [12.0, 45.6], [12.0, 40.1], [22.5, 40.1], [22.5, 36.3], 
        [52.7, 36.3], [52.7, 37.3], [66.6, 37.3], [66.6, 45.6], [12.0, 45.6]
    ])
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
    
    downstairs_correct = []
    mezzanine_correct = []
    
    print("  ✅ Reading CORRECT positioning data from extended dataset...")
    
    for _, row in df.iterrows():
        filename = row['filename']
        file_path = os.path.join(DATA_DIR, filename)
        
        try:
            sample_data = pd.read_csv(file_path, usecols=['tag_x', 'tag_y', 'map_id', 'true_map_id'])
            
            if len(sample_data) > 50:
                sample_data = sample_data.iloc[::5]
            
            # Only include positions where map_id matches true_map_id
            correct_positions = sample_data[sample_data['map_id'] == sample_data['true_map_id']]
            
            for _, pos_row in correct_positions.iterrows():
                x, y, true_map = pos_row['tag_x'], pos_row['tag_y'], pos_row['true_map_id']
                
                if true_map == '682c66de8cde618ce1270230':  # Downstairs
                    downstairs_correct.append([x, y])
                elif true_map == '682c66f08cde618ce127025e':  # Mezzanine
                    mezzanine_correct.append([x, y])
                    
        except Exception as e:
            print(f"Could not read positioning data from {filename}: {e}")
    
    # Plot downstairs correct
    ax1.plot(floor_verts[:, 0], floor_verts[:, 1], 'k-', linewidth=3, label='Floor Plan')
    ax1.fill(floor_verts[:, 0], floor_verts[:, 1], alpha=0.1, color='gray')
    
    if downstairs_correct:
        downstairs_correct = np.array(downstairs_correct)
        ax1.scatter(downstairs_correct[:, 0], downstairs_correct[:, 1], 
                   alpha=0.6, s=1, color='green', label='Correct Positions')
        
    ax1.set_title('Extended Data - Downstairs: CORRECT Positioning', fontsize=14, fontweight='bold')
    ax1.set_xlabel('X Position (meters)')
    ax1.set_ylabel('Y Position (meters)')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    ax1.set_aspect('equal')
    ax1.invert_yaxis()
    
    # Plot mezzanine correct
    ax2.plot(floor_verts[:, 0], floor_verts[:, 1], 'k-', linewidth=3, label='Floor Plan')
    ax2.fill(floor_verts[:, 0], floor_verts[:, 1], alpha=0.1, color='gray')
    
    if mezzanine_correct:
        mezzanine_correct = np.array(mezzanine_correct)
        ax2.scatter(mezzanine_correct[:, 0], mezzanine_correct[:, 1], 
                   alpha=0.6, s=1, color='green', label='Correct Positions')
        
    ax2.set_title('Extended Data - Mezzanine: CORRECT Positioning', fontsize=14, fontweight='bold')
    ax2.set_xlabel('X Position (meters)')
    ax2.set_ylabel('Y Position (meters)')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    ax2.set_aspect('equal')
    ax2.invert_yaxis()
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/correct_positioning.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✅ Plotted {len(downstairs_correct)} correct downstairs and {len(mezzanine_correct)} correct mezzanine positions")

def plot_incorrect_positions(df: pd.DataFrame):
    """Plot only positions where computed map_id doesn't match true_map_id (positioning errors)"""
    # Floor vertices from plotter.py (X, Y coordinates only)
    floor_verts = np.array([
        [12.0, 45.6], [12.0, 40.1], [22.5, 40.1], [22.5, 36.3], 
        [52.7, 36.3], [52.7, 37.3], [66.6, 37.3], [66.6, 45.6], [12.0, 45.6]
    ])
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
    
    downstairs_incorrect = []
    mezzanine_incorrect = []
    
    print("  ❌ Reading INCORRECT positioning data from extended dataset...")
    
    for _, row in df.iterrows():
        filename = row['filename']
        file_path = os.path.join(DATA_DIR, filename)
        
        try:
            sample_data = pd.read_csv(file_path, usecols=['tag_x', 'tag_y', 'map_id', 'true_map_id'])
            
            if len(sample_data) > 50:
                sample_data = sample_data.iloc[::5]
            
            # Only include positions where map_id doesn't match true_map_id
            incorrect_positions = sample_data[sample_data['map_id'] != sample_data['true_map_id']]
            
            for _, pos_row in incorrect_positions.iterrows():
                x, y, true_map = pos_row['tag_x'], pos_row['tag_y'], pos_row['true_map_id']
                
                # Plot on TRUE floor (not computed floor)
                if true_map == '682c66de8cde618ce1270230':  # Actually downstairs
                    downstairs_incorrect.append([x, y])
                elif true_map == '682c66f08cde618ce127025e':  # Actually mezzanine
                    mezzanine_incorrect.append([x, y])
                    
        except Exception as e:
            print(f"Could not read positioning data from {filename}: {e}")
    
    # Plot downstairs incorrect
    ax1.plot(floor_verts[:, 0], floor_verts[:, 1], 'k-', linewidth=3, label='Floor Plan')
    ax1.fill(floor_verts[:, 0], floor_verts[:, 1], alpha=0.1, color='gray')
    
    if downstairs_incorrect:
        downstairs_incorrect = np.array(downstairs_incorrect)
        ax1.scatter(downstairs_incorrect[:, 0], downstairs_incorrect[:, 1], 
                   alpha=0.6, s=1, color='red', label='Incorrect Positions')
        
    ax1.set_title('Extended Data - Downstairs: INCORRECT Positioning', fontsize=14, fontweight='bold')
    ax1.set_xlabel('X Position (meters)')
    ax1.set_ylabel('Y Position (meters)')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    ax1.set_aspect('equal')
    ax1.invert_yaxis()
    
    # Plot mezzanine incorrect
    ax2.plot(floor_verts[:, 0], floor_verts[:, 1], 'k-', linewidth=3, label='Floor Plan')
    ax2.fill(floor_verts[:, 0], floor_verts[:, 1], alpha=0.1, color='gray')
    
    if mezzanine_incorrect:
        mezzanine_incorrect = np.array(mezzanine_incorrect)
        ax2.scatter(mezzanine_incorrect[:, 0], mezzanine_incorrect[:, 1], 
                   alpha=0.6, s=1, color='red', label='Incorrect Positions')
        
    ax2.set_title('Extended Data - Mezzanine: INCORRECT Positioning', fontsize=14, fontweight='bold')
    ax2.set_xlabel('X Position (meters)')
    ax2.set_ylabel('Y Position (meters)')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    ax2.set_aspect('equal')
    ax2.invert_yaxis()
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/incorrect_positioning.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ❌ Plotted {len(downstairs_incorrect)} incorrect downstairs and {len(mezzanine_incorrect)} incorrect mezzanine positions")

def plot_anchor_coverage_analysis(df: pd.DataFrame):
    """Analyze and visualize anchor coverage in the extended dataset"""
    print("  📡 Analyzing anchor coverage in extended dataset...")
    
    anchor_usage_stats = {}
    total_messages = 0
    
    # Get a sample of files to analyze anchor usage
    sample_files = df.sample(min(10, len(df)))  # Sample up to 10 files
    
    for _, row in sample_files.iterrows():
        filename = row['filename']
        file_path = os.path.join(DATA_DIR, filename)
        
        try:
            # Read first 100 rows to get anchor usage patterns
            sample_data = pd.read_csv(file_path, nrows=100)
            
            # Find anchor columns (those ending with _rssi)
            anchor_cols = [col for col in sample_data.columns if col.endswith('_rssi') and len(col) == 17]  # 12 char MAC + "_rssi"
            
            for col in anchor_cols:
                anchor_mac = col[:-5]  # Remove '_rssi'
                
                # Count non-empty RSSI values
                non_empty_count = sample_data[col].notna().sum() - (sample_data[col] == '').sum()
                
                if anchor_mac not in anchor_usage_stats:
                    anchor_usage_stats[anchor_mac] = 0
                anchor_usage_stats[anchor_mac] += non_empty_count
            
            total_messages += len(sample_data)
            
        except Exception as e:
            print(f"Could not analyze anchor usage from {filename}: {e}")
    
    if anchor_usage_stats:
        # Create visualization
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Sort anchors by usage
        sorted_anchors = sorted(anchor_usage_stats.items(), key=lambda x: x[1], reverse=True)
        
        # Top 20 most active anchors
        top_20 = sorted_anchors[:20]
        anchor_names = [f"{mac[:6]}..." for mac, count in top_20]
        counts = [count for mac, count in top_20]
        
        bars = ax1.bar(range(len(top_20)), counts, color='steelblue')
        ax1.set_title('Extended Data: Top 20 Most Active Anchors', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Anchor MAC (truncated)')
        ax1.set_ylabel('Usage Count')
        ax1.set_xticks(range(len(top_20)))
        ax1.set_xticklabels(anchor_names, rotation=45, ha='right')
        ax1.grid(True, alpha=0.3)
        
        # Histogram of anchor usage
        usage_values = list(anchor_usage_stats.values())
        ax2.hist(usage_values, bins=20, alpha=0.7, color='lightcoral', edgecolor='black')
        ax2.set_title('Extended Data: Anchor Usage Distribution', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Usage Count')
        ax2.set_ylabel('Number of Anchors')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{OUTPUT_DIR}/anchor_coverage_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  📡 Analyzed {len(anchor_usage_stats)} unique anchors")
        print(f"  📊 Most active anchor: {sorted_anchors[0][0]} ({sorted_anchors[0][1]} uses)")
        print(f"  📊 Average anchor usage: {np.mean(usage_values):.1f}")

def generate_summary_report(df: pd.DataFrame, floor_stats=None):
    """Generate a text summary report"""
    total_files = len(df)
    total_messages = df['message_count'].sum()
    total_size_mb = df['size_mb'].sum()
    
    downstairs_count = len(df[df['floor'] == 0])
    mezzanine_count = len(df[df['floor'] == 1])
    
    report = f"""
📊 EXTENDED ML TRAINING DATA ANALYSIS REPORT
{'='*60}

 DATASET OVERVIEW (Extended Format):
   - Total CSV files: {total_files}
   - Total messages collected: {total_messages:,}
   - Total data size: {total_size_mb:.1f} MB
   - Average messages per tag: {total_messages/total_files:.0f}
   - Data source: {DATA_DIR}/

 FLOOR DISTRIBUTION:
   - Downstairs tags: {downstairs_count}
   - Mezzanine tags: {mezzanine_count}

 MESSAGE STATISTICS:
   - Highest message count: {df['message_count'].max():,} (Tag: {df.loc[df['message_count'].idxmax(), 'tag_mac'][:12]}...)
   - Lowest message count: {df['message_count'].min():,} (Tag: {df.loc[df['message_count'].idxmin(), 'tag_mac'][:12]}...)
   - Median message count: {df['message_count'].median():.0f}
   - Standard deviation: {df['message_count'].std():.0f}

 FILE SIZE STATISTICS:
   - Largest file: {df['size_mb'].max():.1f} MB
   - Smallest file: {df['size_mb'].min():.1f} MB
   - Average file size: {df['size_mb'].mean():.1f} MB

 DATA QUALITY:
   - Files with >1000 messages: {len(df[df['message_count'] > 1000])} ({len(df[df['message_count'] > 1000])/total_files*100:.1f}%)
   - Files with >2000 messages: {len(df[df['message_count'] > 2000])} ({len(df[df['message_count'] > 2000])/total_files*100:.1f}%)
   - Files with <500 messages: {len(df[df['message_count'] < 500])} ({len(df[df['message_count'] < 500])/total_files*100:.1f}%)

 EXTENDED DATA FEATURES:
   - Comprehensive anchor data (~240 anchors per message)
   - Real anchor coordinates from database
   - Enhanced positioning metadata
   - Compatible with ml_training_data/ format

 Generated visualizations saved to: {OUTPUT_DIR}/
   - message_distribution.png
   - spatial_distribution.png  
   - correct_positioning.png
   - incorrect_positioning.png
   - anchor_coverage_analysis.png

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    # Save report to file
    with open(f'{OUTPUT_DIR}/analysis_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(report)

def main():
    """Main execution function"""
    print("🎨 Starting Extended ML Training Data Visualization")
    print("📊 Analyzing ml_training_data_exte_new/ folder")
    print("=" * 60)
    
    # Create output directory
    create_output_dir()
    
    # Get file statistics
    print("📊 Analyzing extended CSV files...")
    df = get_file_stats()
    
    if len(df) == 0:
        print(f"❌ No CSV files found in {DATA_DIR}/ directory!")
        return
    
    print(f"✅ Found {len(df)} CSV files in extended dataset")
    print(f"📈 Total messages: {df['message_count'].sum():,}")
    print(f"💾 Total data size: {df['size_mb'].sum():.1f} MB")
    
    # Generate visualizations
    print("\n🎨 Generating extended data visualizations...")
    
    print("  📊 Creating message distribution plots...")
    plot_message_distribution(df)
    
    print("  🗺️  Creating spatial distribution maps...")
    plot_spatial_distribution(df)
    
    print("  ✅ Creating correct positioning analysis...")
    plot_correct_positions(df)
    
    print("  ❌ Creating incorrect positioning analysis...")
    plot_incorrect_positions(df)
    
    print("  📡 Creating anchor coverage analysis...")
    plot_anchor_coverage_analysis(df)
    
    print("  📝 Generating summary report...")
    generate_summary_report(df, None)
    
    print(f"\n✅ All extended data visualizations completed!")
    print(f"📁 Check the '{OUTPUT_DIR}/' folder for all plots and reports")
    print(f"🎯 Extended format includes ~240 anchor columns with real coordinates")

if __name__ == "__main__":
    main() 