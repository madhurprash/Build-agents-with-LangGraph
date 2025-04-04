FROM public.ecr.aws/lambda/python:3.11

# Copy requirements file
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install -U boto3 botocore

# Copy function code and data
COPY deploy_langGraph_agent/server.py ${LAMBDA_TASK_ROOT}/lambda_function.py
# This is the data that the lambda function requires that is a substitution for actual
# API calls. This data contains synthetic data that is used to test the tool calling functionality in
# langGraph
COPY data ${LAMBDA_TASK_ROOT}/data
COPY deploy_langGraph_agent/__init__.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD [ "lambda_function.handler" ]