from google.cloud import storage, bigquery


def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """Upload file to Google Cloud Storage."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    print(f"File {source_file_name} uploaded to {destination_blob_name}.")


def store_in_bigquery(dataset_id, table_id, structured_data):
    """Store structured data in BigQuery."""
    client = bigquery.Client()
    table_ref = f"{client.project}.{dataset_id}.{table_id}"
    errors = client.insert_rows_json(table_ref, [structured_data])
    if errors:
        print(f"Error inserting data into BigQuery: {errors}")
    else:
        print("Data successfully inserted into BigQuery.")
