#!/bin/bash
# Filter gcov output to show only project source files (not test files)

while IFS= read -r line; do
    # Check if this is a File line
    if [[ "$line" =~ ^File\ \'.*\'$ ]]; then
        # Extract filename
        filename=$(echo "$line" | sed "s/File '\(.*\)'/\1/")
        
        # Check if it's a project source file (not a test file)
        if [[ "$filename" == "common.c" ]] || \
           [[ "$filename" == "query_analyzer.c" ]] || \
           [[ "$filename" == "metrics_engine.c" ]] || \
           [[ "$filename" == "test_orchestrator.c" ]] || \
           [[ "$filename" == "performance_monitor.c" ]]; then
            
            # Print the file line
            echo "$line"
            
            # Read and print next 4 lines (coverage data)
            for i in {1..4}; do
                if IFS= read -r nextline; then
                    echo "$nextline"
                fi
            done
            echo ""
        fi
    fi
done