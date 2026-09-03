import os
from minio import Minio
from minio.versioningconfig import VersioningConfig, ENABLED


# 1. Initialize MinIO Client
client = Minio(
    "localhost:9000",
    access_key="admin",
    secret_key="password1234",
    secure=False
)

bucket_name = "profile-version-demo"

# 2. Check and Create Bucket
if not client.bucket_exists(bucket_name):
    client.make_bucket(bucket_name)

# 3. Enable Versioning on Bucket
client.set_bucket_versioning(bucket_name, VersioningConfig(ENABLED))
print(f"[SUCCESS] Versioning enabled on bucket: '{bucket_name}'\n")

# 4. Upload First Image (Version 1)
print("--- Step 1: Uploading Version 1 ---")
v1_result = client.fput_object(bucket_name, "my_profile.jpg", "./photo_v1.jpg")
v1_id = v1_result.version_id
print(f"Uploaded photo_v1.jpg -> Version ID: {v1_id}\n")

# 5. Upload Second Image with SAME Object Name (Version 2)
print("--- Step 2: Uploading Version 2 (Overwriting) ---")
v2_result = client.fput_object(bucket_name, "my_profile.jpg", "./photo_v2.jpg")
v2_id = v2_result.version_id
print(f"Uploaded photo_v2.jpg -> Version ID: {v2_id}\n")

# 6. Test Download without Version ID (Latest Version)
print("--- Step 3: Downloading WITHOUT specifying version_id ---")
client.fget_object(bucket_name, "my_profile.jpg", "./downloaded_default.jpg")
print("Downloaded to './downloaded_default.jpg' (Should be Version 2)\n")

# 7. Test Download WITH Version ID (Specific Version - Version 1)
print("--- Step 4: Downloading WITH specific version_id (V1) ---")
client.fget_object(bucket_name, "my_profile.jpg", "./downloaded_v1.jpg", version_id=v1_id)
print(f"Downloaded Version 1 ({v1_id}) to './downloaded_v1.jpg'\n")