from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from django.conf import settings
from qcloud_cos import CosServiceError


def create_bucket(bucket_name, bucket_region='ap-beijing'):
    secret_id = settings.COS_SECRET_ID
    secret_key = settings.COS_SECRET_KEY
    config = CosConfig(Region=bucket_region, SecretId=secret_id, SecretKey=secret_key)
    client = CosS3Client(config)
    try:
        client.create_bucket(
            Bucket=bucket_name,
            ACL="public-read"
        )
    except CosServiceError as e:
        print(e.get_resource_location(), e.get_error_msg())


def upload_file(bucket_name, bucket_region, file_object, key):
    secret_id = settings.COS_SECRET_ID
    secret_key = settings.COS_SECRET_KEY
    config = CosConfig(Region=bucket_region, SecretId=secret_id, SecretKey=secret_key)
    client = CosS3Client(config)
    client.upload_file_from_buffer(
        Bucket=bucket_name,
        Body=file_object,  # 文件对象
        Key=key  # 上传到桶之后的文件名
    )
    # 腾讯云桶存储文件的网址https://18846826671-1591803114-1301997034.cos.ap-beijing.myqcloud.com/7656bb7adcec81d4241b90e950ccdad9.jpeg
    return "https://{}.cos.{}.myqcloud.com/{}".format(bucket_name, bucket_region, key)


def delete_file(bucket_name, bucket_region, key):
    secret_id = settings.COS_SECRET_ID
    secret_key = settings.COS_SECRET_KEY
    config = CosConfig(Region=bucket_region, SecretId=secret_id, SecretKey=secret_key)
    client = CosS3Client(config)
    client.delete_object(
        Bucket=bucket_name,
        Key=key,
    )


def delete_file_list(bucket_name, bucket_region, key_list):
    secret_id = settings.COS_SECRET_ID
    secret_key = settings.COS_SECRET_KEY
    config = CosConfig(Region=bucket_region, SecretId=secret_id, SecretKey=secret_key)
    client = CosS3Client(config)
    objects = {
        "Quiet": "true",
        "Object": key_list
    }
    client.delete_objects(
        Bucket=bucket_name,
        Delete=objects
    )
