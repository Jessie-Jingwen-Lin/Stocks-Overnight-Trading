#!/bin/bash
cd downloader
gcloud builds submit --tag gcr.io/overnight-stock-trading/downloader

gcloud beta run deploy yf-0 \
  --image=gcr.io/overnight-stock-trading/downloader \
  --concurrency=1 \
  --timeout=3600 \
  --cpu=1 \
  --max-instances=1 \
  --platform=managed \
  --region=us-central1 \
  --project=overnight-stock-trading