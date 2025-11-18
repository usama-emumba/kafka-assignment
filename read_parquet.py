import pandas as pd
from minio import Minio
import io
import json
import sys
import glob

# Configure pandas display options for full output
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

# MinIO connection
client = Minio(
    "localhost:9000",
    access_key="admin",
    secret_key="password123",
    secure=False
)

def response(success, message, data=None, error=None):
    """Standard response format for all functions"""
    result = {
        "success": success,
        "message": message
    }
    if data is not None:
        result["data"] = data
    if error:
        result["error"] = str(error)
    return result

def print_dataframe_full(df, title="Data"):
    """Print DataFrame in full tabular format"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")
    
    if df is None or len(df) == 0:
        print("No data to display")
        return
    
    # Print shape
    print(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns\n")
    
    # Print full DataFrame
    print(df.to_string(index=True))
    
    # Print data types
    print(f"\n{'-'*80}")
    print("Data Types:")
    print(f"{'-'*80}")
    for col, dtype in df.dtypes.items():
        print(f"  {col:30s} {dtype}")

def list_parquet_files(topic):
    """List all Parquet files for a topic"""
    try:
        objects = client.list_objects("my-data-lake", prefix=f"topics/{topic}/", recursive=True)
        files = [obj.object_name for obj in objects if obj.object_name.endswith('.parquet')]
        
        print(f"\n{topic} files: {len(files)} found")
        for i, f in enumerate(files[:10], 1):
            print(f"  {i}. {f}")
        if len(files) > 10:
            print(f"  ... and {len(files) - 10} more")
        
        return response(True, f"Found {len(files)} files", data=files)
    except Exception as e:
        return response(False, f"Failed to list files for topic: {topic}", error=e)

def extract_after_data(df):
    """Extract data from Debezium CDC 'after' field"""
    if 'after' not in df.columns:
        return df
    
    # Extract 'after' field (contains actual row data)
    after_data = df['after'].apply(lambda x: x if isinstance(x, dict) else {})
    
    # Convert to DataFrame
    extracted_df = pd.DataFrame(after_data.tolist())
    
    # Add CDC metadata
    if 'op' in df.columns:
        extracted_df['_cdc_operation'] = df['op']
    if 'ts_ms' in df.columns:
        extracted_df['_cdc_timestamp'] = pd.to_datetime(df['ts_ms'], unit='ms')
    
    return extracted_df

def read_parquet_from_minio(file_path):
    """Read a Parquet file from MinIO"""
    try:
        response_obj = client.get_object("my-data-lake", file_path)
        df = pd.read_parquet(io.BytesIO(response_obj.read()))
        
        # Extract actual data from CDC format
        df = extract_after_data(df)
        
        print(f"\n{'='*80}")
        print(f"File: {file_path}")
        print(f"{'='*80}")
        print_dataframe_full(df, f"Data from {file_path.split('/')[-1]}")
        
        return response(True, "File read successfully", data=df)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return response(False, f"Failed to read file: {file_path}", error=e)

def read_from_path(path):
    """Read Parquet files from MinIO path with wildcard support"""
    try:
        # If just a filename, search for it
        if '/' not in path and path.endswith('.parquet'):
            print(f"Searching for file: {path}")
            all_objects = client.list_objects("my-data-lake", prefix="topics/", recursive=True)
            files = [obj.object_name for obj in all_objects if obj.object_name.endswith(path)]
            if not files:
                print(f"File not found: {path}")
                print("\nAvailable files (first 10):")
                for i, obj in enumerate(list(client.list_objects("my-data-lake", prefix="topics/", recursive=True))[:10], 1):
                    if obj.object_name.endswith('.parquet'):
                        print(f"  {i}. {obj.object_name}")
                return response(False, f"File not found: {path}")
        elif '*' in path:
            # Handle wildcard
            prefix = path.split('*')[0].replace('topics/', '')
            objects = client.list_objects("my-data-lake", prefix=f"topics/{prefix}", recursive=True)
            files = [obj.object_name for obj in objects if obj.object_name.endswith('.parquet')]
        else:
            # Full path or folder
            if path.endswith('.parquet'):
                # Full path to specific file
                if not path.startswith('topics/'):
                    path = f"topics/{path}"
                files = [path]
            else:
                # Folder path
                if not path.startswith('topics/'):
                    path = f"topics/{path}"
                objects = client.list_objects("my-data-lake", prefix=path, recursive=True)
                files = [obj.object_name for obj in objects if obj.object_name.endswith('.parquet')]
        
        print(f"\n{'='*80}")
        print(f"Reading {len(files)} file(s) from: {path}")
        print(f"{'='*80}")
        
        dfs = []
        for file_path in files[:20]:  # Read first 20 files
            result = read_parquet_from_minio(file_path)
            if result['success'] and result['data'] is not None and len(result['data']) > 0:
                dfs.append(result['data'])
        
        if dfs:
            combined = pd.concat(dfs, ignore_index=True)
            print_dataframe_full(combined, f"Combined Data - Total Rows: {len(combined)}")
            
            # PII Masking Verification
            if 'email' in combined.columns:
                print(f"\n{'='*80}")
                print("PII Masking Verification")
                print(f"{'='*80}")
                
                verification_df = pd.DataFrame({
                    'Field': ['Email', 'Phone', 'Address'],
                    'Sample Values': [
                        combined['email'].head().tolist() if 'email' in combined.columns else 'N/A',
                        combined['phone'].head().tolist() if 'phone' in combined.columns else 'N/A',
                        combined['address'].head().tolist() if 'address' in combined.columns else 'N/A'
                    ]
                })
                print(verification_df.to_string(index=False))
                
                # Check if masking is applied
                print(f"\n{'='*80}")
                print("Masking Status:")
                print(f"{'='*80}")
                email_masked = combined['email'].str.contains('MASKED').any() if 'email' in combined.columns else False
                phone_masked = combined['phone'].str.contains(r'\*').any() if 'phone' in combined.columns else False  # Fixed: Added r prefix
                address_masked = combined['address'].str.contains('REDACTED').any() if 'address' in combined.columns else False
                
                status_df = pd.DataFrame({
                    'Field': ['Email', 'Phone', 'Address'],
                    'Masked': [
                        'YES' if email_masked else 'NO',
                        'YES' if phone_masked else 'NO',
                        'YES' if address_masked else 'NO'
                    ]
                })
                print(status_df.to_string(index=False))
            
            return response(True, f"Successfully read {len(files)} files", data=combined)
        
        return response(False, "No data found in files")
    except Exception as e:
        return response(False, f"Failed to read from path: {path}", error=e)

def read_all_files_for_topic(topic):
    """Read all Parquet files for a topic and combine"""
    result = list_parquet_files(topic)
    
    if not result['success']:
        return result
    
    files = result['data']
    
    if not files:
        return response(False, f"No files found for topic: {topic}")
    
    dfs = []
    for file_path in files[:20]:  # Read first 20 files
        file_result = read_parquet_from_minio(file_path)
        if file_result['success'] and file_result['data'] is not None and len(file_result['data']) > 0:
            dfs.append(file_result['data'])
    
    if dfs:
        combined = pd.concat(dfs, ignore_index=True)
        print_dataframe_full(combined, f"Combined Data for {topic.upper()}")
        
        # PII Masking Verification
        if 'email' in combined.columns:
            print(f"\n{'='*80}")
            print("PII Masking Verification")
            print(f"{'='*80}")
            
            # Show sample values in table format
            sample_df = combined[['email', 'phone', 'address']].head() if all(col in combined.columns for col in ['email', 'phone', 'address']) else combined[['email']].head() if 'email' in combined.columns else None
            
            if sample_df is not None:
                print("\nSample Values:")
                print(sample_df.to_string(index=True))
        
        return response(True, f"Successfully processed {len(files)} files", data=combined)
    
    return response(False, "No data found in files")

# Example usage
if __name__ == "__main__":
    print(f"\n{'='*80}")
    print("CDC Data Lake Parquet Reader")
    print(f"{'='*80}\n")
    
    if len(sys.argv) > 1:
        # Read from command line path
        path = sys.argv[1]
        result = read_from_path(path)
        
        if result['success']:
            print(f"\nSuccess: {result['message']}")
        else:
            print(f"\nError: {result['message']}")
            if 'error' in result:
                print(f"   Details: {result['error']}")
    else:
        # Default: Read all topics
        for topic in ["customers", "products", "orders", "order_items"]:
            print("\n" + "=" * 80)
            print(f"{topic.upper()} DATA")
            print("=" * 80)
            result = read_all_files_for_topic(topic)
            
            if not result['success']:
                print(f"Error: {result['message']}")
