#!/bin/bash

echo 
echo '=======================Vrika Clean Script for Unix======================='
echo 'Running this script will delete the scan database, all files uploaded and generated.'

script_path=$(basename "$(dirname "$0")")
vrika_home="$HOME/.Vrika"

# Ensure the script is run from the correct directory
if [[ "$script_path" != "scripts" ]]; then
    echo 'Please run this script from the Vrika directory:'
    echo './scripts/clean.sh'
    exit 1
fi

# Confirmation prompt
VAL=${1:-}
if [[ -z "$VAL" ]]; then
    read -p 'Continue? (Y/N): ' confirm
    [[ $confirm =~ ^[yY]([eE][sS])?$ ]] || exit 1
    VAL=$confirm
fi

echo
if [[ "$VAL" =~ ^[yY]$ ]]; then
    echo 'Cleaning up Vrika directories and files...'

    # Remove files from key directories
    rm -rf ./vrika_mobile_security/{uploads,downloads,StaticAnalyzer/migrations,DynamicAnalyzer/migrations,Vrika/migrations}/*
    
    echo 'Removing Python bytecode and cache files'
    find ./ -type f -name "*.pyc" -o -name "*.pyo" -delete
    find ./ -type d -name "__pycache__" -exec rm -rf {} +

    # Remove temporary, log, and database files
    echo 'Deleting temporary, log, and database files'
    rm -f ./vrika_mobile_security/debug.log ./classes* ./vrika_mobile_security/db.sqlite3 ./vrika_mobile_security/secret

    # Remove the Vrika data directory if it exists
    if [[ -d "$vrika_home" ]]; then
        echo "Deleting Vrika data directory: $vrika_home"
        rm -rf "$vrika_home"
    fi

    echo 'Cleanup complete.'
fi
