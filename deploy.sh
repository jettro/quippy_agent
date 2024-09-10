#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status.

# Directory where the lambda functions are located
LAMBDA_DIR="lambda"

# Create a package directory for the dependencies layer
LAYER_DIR="$LAMBDA_DIR/dependencies_layer"
mkdir -p "$LAYER_DIR"

# Export dependencies using Poetry
poetry export -f requirements.txt --output $LAYER_DIR/requirements.txt

# Install dependencies into the layer directory
pip install -r $LAYER_DIR/requirements.txt -t $LAYER_DIR/python

# Create a package directory for each lambda function
for app in $(ls $LAMBDA_DIR/*.py); do
    # Get the base name of the lambda function (e.g., app1, app2)
    app_name=$(basename "$app" .py)
    
    # Create a directory for the packaged lambda
    package_dir="$LAMBDA_DIR/${app_name}_package"
    mkdir -p "$package_dir"

    # Copy the lambda function into the package directory
    cp $LAMBDA_DIR/$app_name.py $package_dir/app.py

    echo "Packaged $app_name in $package_dir"
done

# Deploy the CDK stacks
cdk deploy