# Mushroom Demand Forecasting & Decision Intelligence System

## Overview
This system provides production-grade demand forecasting for perishable mushrooms, reducing wastage and optimizing profits. It includes:
- **Multi-Model Inference**: B2B (XGBoost), B2C (LSTM), Price Elasticity, and Intraday Correction.
- **Feature Store**: Feast-ready definitions for historical and real-time features.
- **Dashboard**: Streamlit-based UI for forecasting, pricing simulation, and explainability.
- **MLOps**: Dockerized services and Kubernetes manifests.

## Project Structure
- `data_generation.py`: Generates synthetic training (`historical_sales.csv`) and telemetry (`intraday_telemetry.csv`) data.
- `features/`: Feature engineering pipeline and Feast definitions.
- `models/`: Training scripts for all models.
- `serve/`: FastAPI application for serving predictions.
- `dashboard/`: Streamlit dashboard for visualization.
- `mlops/`: Kubernetes manifests and monitoring config.

## Setup & Run

### 1. Generate Data
```bash
python data_generation.py
```

### 2. Engineer Features
```bash
python features/engineer_features.py
```

### 3. Train Models
```bash
python models/train_b2b.py
python models/train_b2c.py
python models/train_elasticity.py
python models/train_intraday.py
```

### 4. Run API (Serving)
```bash
cd serve
uvicorn app:app --reload
```
API will be available at `http://localhost:8000`.

### 5. Run Dashboard
```bash
streamlit run dashboard/app.py
```
Dashboard will be available at `http://localhost:8501`.

## Docker & Kubernetes
Build images:
```bash
docker build -t mushroom-api:latest -f serve/Dockerfile .
docker build -t mushroom-dashboard:latest -f dashboard/Dockerfile .
```

Deploy to K8s:
```bash
kubectl apply -f mlops/k8s_deployment.yaml
```
