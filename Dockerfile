FROM public.ecr.aws/lambda/python:3.12

# Set working directory
WORKDIR /var/task

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt --target .

# Copy application code
COPY . .

# Set the Lambda handler
CMD ["handler.lambda_handler"]
