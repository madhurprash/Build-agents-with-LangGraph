FROM public.ecr.aws/lambda/python:3.11

# Copy requirements file
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install/upgrade specific dependencies if needed
RUN pip install -U boto3 botocore

# Install Mangum for AWS Lambda integration
RUN pip install mangum

# Copy function code and data
COPY 3_build_and_deploy_agent.py ${LAMBDA_TASK_ROOT}/lambda_function.py
COPY data/ ${LAMBDA_TASK_ROOT}/data/

# Set the CMD to your handler
CMD ["lambda_function.handler"]