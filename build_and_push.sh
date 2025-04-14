#!/bin/bash

# Exit on error
set -e

# Load environment variables from .env (if it exists)
if [ -f .env ]; then
  echo "🔑 Loading environment variables from .env..."
  # Export all variables; this assumes your .env does not contain spaces or special characters
  export $(grep -v '^#' .env | xargs)
fi

# Configuration
AWS_REGION="us-west-2"
ECR_REPO_NAME="newrepo"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME"

echo "🔐 Logging in to Amazon ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

# Create repository if it doesn't exist
echo "📦 Creating ECR repository if it doesn't exist..."
aws ecr describe-repositories --repository-names "$ECR_REPO_NAME" --region "$AWS_REGION" || \
    aws ecr create-repository --repository-name "$ECR_REPO_NAME" --region "$AWS_REGION"

# Build the Docker image without guardrails token
echo "🏗️  Building Docker image..."
# docker build -t "$ECR_REPO_NAME" .
docker build --platform linux/amd64 -t "$ECR_REPO_NAME" .

# Tag the image
echo "🏷️  Tagging image..."
docker tag "$ECR_REPO_NAME":latest "$ECR_REPO_URI":latest

# Push the image to ECR
echo "⬆️  Pushing image to ECR..."
docker push "$ECR_REPO_URI":latest

echo "✅ Successfully built and pushed image to:"
echo "$ECR_REPO_URI:latest"