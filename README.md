# RTLS Floor Selection ML Training Data Generation

A comprehensive data collection and analysis system for improving Real-Time Location System (RTLS) floor detection accuracy through machine learning. This project addresses a critical challenge in multi-floor positioning systems by generating extensive training datasets to power an XGBoost-based floor selection model.

## Project Overview

This repository contains tools for collecting, processing, and analyzing RTLS positioning data to train machine learning models that correct floor selection errors in multi-floor environments. The system was developed to solve floor misclassification issues where tags were incorrectly assigned to the wrong floor level, significantly improving positioning accuracy and system reliability.

## Primary Objective: ML Training Data Generation

The main purpose of this project is to generate comprehensive CSV datasets that feed into an XGBoost machine learning model designed to fix floor selection errors. The system collects real-time positioning data from 60 strategically placed tags across two floors (ground floor and mezzanine), capturing detailed signal characteristics and spatial information that enable the ML model to learn patterns and make accurate floor predictions.

### Key Achievements

- **Large-Scale Data Collection**: Generated training datasets with thousands of samples per tag, capturing diverse positioning scenarios and signal conditions
- **Comprehensive Feature Engineering**: Extracted rich feature sets including RSSI measurements, anchor positions, distance calculations, covariance matrices, and per-floor statistical aggregations
- **Production-Ready ML Integration**: The generated datasets directly feed into an XGBoost model deployed in production, achieving 99.96% validation accuracy on 121,383 training samples
- **Real-Time Data Processing**: Automated data collection pipeline that processes live MQTT positioning streams and transforms them into structured training data

### Data Collection Process

The system operates by:

1. **Real-Time Monitoring**: Connects to MQTT brokers to receive live positioning data from the RTLS engine
2. **Tag Management**: Monitors 60 positioning tags (30 per floor) with known ground truth floor assignments
3. **Feature Extraction**: For each position measurement, extracts:
   - Position coordinates (x, y) and covariance matrices
   - RSSI (signal strength) measurements from all anchors
   - Anchor positions, distances, and usage status
   - Per-floor statistical aggregations (mean, max, min, std deviation of RSSI)
   - Signal quality indicators
4. **Data Labeling**: Automatically labels each sample with the true floor assignment for supervised learning
5. **CSV Generation**: Writes structured CSV files (one per tag) ready for ML model training

### Dataset Characteristics

- **Scale**: Each tag generates thousands of training samples (up to 8,500 rows per tag in extended format)
- **Features**: Hundreds of features per sample including anchor-specific RSSI values, spatial statistics, and signal quality metrics
- **Coverage**: Data collected across multiple deployment scenarios, time periods, and environmental conditions
- **Quality**: Ground truth labels ensure high-quality training data for supervised learning

## Secondary Objective: Position Estimation Accuracy Evaluation

Additionally, the project includes tools for evaluating the accuracy of the RTLS positioning system. The `floor_success_rate.py` script provides comprehensive validation capabilities:

- **Success Rate Calculation**: Tracks positioning accuracy rates overall and per floor
- **Real-Time Monitoring**: Validates that tags are detected on their correct floors
- **Performance Metrics**: Provides detailed statistics including message distribution, response rates, and non-responsive tag identification
- **Quality Assurance**: Essential for validating RTLS deployment quality and identifying positioning issues

## Technical Implementation

### Data Generation Scripts

- **`generate_ml_data.py`**: Core script for generating ML training data with standard feature set
- **`generate_ml_data_exte.py`**: Extended version supporting ~240 anchor MACs with enhanced feature extraction
- **Automated Processing**: Handles MQTT message parsing, feature engineering, and CSV file management
- **Incremental Collection**: Supports appending to existing datasets, enabling continuous data collection

### Data Output

Training data is organized as:
- **`ml_training_data_new/`**: Standard format training datasets (one CSV per tag)
- **`ml_training_data_exte_new/`**: Extended format with additional anchor coverage

Each CSV file contains:
- Position and timestamp information
- Covariance matrices for uncertainty quantification
- Per-map statistics (anchor counts, RSSI aggregations)
- Per-anchor detailed measurements (RSSI, position, distance, signal quality)
- Ground truth floor labels

### Visualization and Analysis

The project includes visualization tools to analyze the collected data:
- Spatial distribution plots
- Message distribution analysis
- Correct vs. incorrect positioning visualizations
- Floor success rate spatial analysis

## Business Impact

This project directly addresses a critical production issue where floor misclassification was causing incorrect positioning data. By generating comprehensive training datasets and enabling ML-based floor detection:

- **Improved Accuracy**: The resulting XGBoost model achieves 99.96% accuracy in floor selection
- **Production Deployment**: The model is integrated into the live RTLS system, improving real-world positioning reliability
- **Scalable Solution**: The data collection pipeline can be extended to new deployments and environments
- **Cost Reduction**: Automated data collection eliminates manual labeling efforts

## Usage

### Generating ML Training Data

1. Ensure dependencies are installed:
   ```bash
   pip install paho-mqtt requests pandas numpy
   ```

2. Configure MQTT broker and API endpoints in the script

3. Run the data generation script:
   ```bash
   python generate_ml_data.py
   # or for extended format:
   python generate_ml_data_exte.py
   ```

4. Training data will be written to CSV files in the output directory

### Evaluating Position Accuracy

Run the floor success rate evaluation:
```bash
python floor_success_rate.py
```

## Requirements

- Python 3.6+
- paho-mqtt (MQTT client)
- requests (HTTP client for API calls)
- pandas (data processing)
- numpy (numerical operations)
- Access to RTLS MQTT broker and REST API

## Project Structure

```
├── generate_ml_data.py          # Standard ML data generation
├── generate_ml_data_exte.py    # Extended ML data generation
├── floor_success_rate.py        # Position accuracy evaluation
├── visualize_ml_data.py         # Data visualization tools
├── ml_training_data_new/        # Standard format training data
├── ml_training_data_exte_new/   # Extended format training data
└── visualizations/              # Analysis plots and charts
```

## Results

The ML model trained on this data successfully addresses floor selection errors in production, demonstrating the value of comprehensive data collection and feature engineering for RTLS positioning systems. The project showcases the complete pipeline from raw positioning data to production-ready ML model deployment.
