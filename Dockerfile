FROM public.ecr.aws/lambda/python:3.11

# Copy requirements file
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install/upgrade specific dependencies if needed
RUN pip install -U boto3 botocore

# Copy application code and data
COPY *.py ${LAMBDA_TASK_ROOT}/
COPY data/ ${LAMBDA_TASK_ROOT}/data/

# Set the lambda handler
CMD ["3_build_and_deploy_agent.fastAPI_app"]