#!/bin/bash
set -e

cd downloader
gcloud builds submit --tag gcr.io/overnight-stock-trading/downloader


for deploy_region in \
  us-central1 \
  us-east1 \
  us-east4 \
  us-west1 \
  us-west2 \
  us-west3 \
  us-west4 \
  asia-east1 \
  asia-northeast1 \
  asia-northeast2 \
  europe-north1 \
  europe-west1 \
  europe-west4 \
  asia-east2 \
  asia-northeast3 \
  asia-southeast1
do
  echo "Deploying to $deploy_region:"
  gcloud beta run deploy yf-0 \
    --image=gcr.io/overnight-stock-trading/downloader \
    --memory=2048Mi \
    --concurrency=1 \
    --timeout=3600 \
    --cpu=1 \
    --max-instances=32 \
    --platform=managed \
    --project=overnight-stock-trading \
    --region=$deploy_region
  echo ""
  echo ""
  echo ""
done


