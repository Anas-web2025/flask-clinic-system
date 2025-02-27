#!/bin/bash
echo "Installing ODBC Driver 17 for SQL Server..."
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
sudo add-apt-repository "$(curl -fsSL https://packages.microsoft.com/config/ubuntu/20.04/prod.list)"
sudo apt-get update
sudo apt-get install -y msodbcsql17 unixodbc-dev
echo "ODBC Driver installed successfully!"
