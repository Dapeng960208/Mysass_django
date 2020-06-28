from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from django.conf import settings
from qcloud_cos import CosServiceError
from sts.sts import Sts


def create_bucket(bucket_name, bucket_region='ap-beijing'):
    secret_id = settings.COS_SECRET_ID
    secret_key = settings.COS_SECRET_KEY
    config = CosConfig(Region=bucket_region, SecretId=secret_id, SecretKey=secret_key)
    client = CosS3Client(config)

    client.create_bucket(Bucket=bucket_name, ACL="public-read")
    # 为每个桶设置跨域要求
    cors_config = {
        'CORSRule': [
            {
                'MaxAgeSeconds': 500,
                'AllowedOrigin': ['*'],
                'AllowedMethod': ["GET", "PUT", "HEAD", "POST", "DELETE"],
                'AllowedHeader': ['*'],
                'ExposeHeader': ["*"]
            }
        ]
    }

    client.put_bucket_cors(Bucket=bucket_name,
                           CORSConfiguration=cors_config)


def delete_bucket(bucket_name, bucket_region='ap-beijing'):
    """
    删除桶
    先删除桶中的文件，再删除桶中的碎片，再删除空桶
    """
    secret_id = settings.COS_SECRET_ID
    secret_key = settings.COS_SECRET_KEY
    config = CosConfig(Region=bucket_region, SecretId=secret_id, SecretKey=secret_key)
    client = CosS3Client(config)
    try:
        # 找到所有文件下的对象 删除所有的对象
        while True:
            all_objs = client.list_objects(bucket_name)
            contents = all_objs.get('Contents')
            if not contents:
                break
            Delete = {'Object': [{'Key': item['Key']} for item in contents]}
            client.delete_objects(
                Bucket=bucket_name,
                Delete=Delete
            )
            if all_objs['IsTruncated'] == "false":
                break
        # 找到所有的文件碎片 删除所有的文件碎片
        while True:
            part_uploads = client.list_multipart_uploads(bucket_name)
            uploads = part_uploads.get('Upload')
            if not uploads:
                break
            for item in uploads:
                client.abort_multipart_upload(bucket_name, item['Key'], item['UploadId'])
            if part_uploads['IsTruncated'] == "false":
                break
            client.delete_bucket(bucket_name)
    except CosServiceError as e:
        pass


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


def get_cos_credential(bucket_name, bucket_region):
    config = {
        # 临时密钥有效时长，单位是秒
        'duration_seconds': 60,
        'secret_id': settings.COS_SECRET_ID,
        # 固定密钥
        'secret_key': settings.COS_SECRET_KEY,
        # 换成你的 bucket
        'bucket': bucket_name,
        # 换成 bucket 所在地区
        'region': bucket_region,
        # 这里改成允许的路径前缀，可以根据自己网站的用户登录态判断允许上传的具体路径
        # 例子： a.jpg 或者 a/* 或者 * (使用通配符*存在重大安全风险, 请谨慎评估使用)
        'allow_prefix': '*',
        # 密钥的权限列表。简单上传和分片需要以下的权限，其他权限列表请看 https://cloud.tencent.com/document/product/436/31923
        'allow_actions': [
            # 简单上传
            'name/cos:PutObject',
            'name/cos:PostObject',
            # 分片上传
            # 'name/cos:InitiateMultipartUpload',
            # 'name/cos:ListMultipartUploads',
            # 'name/cos:ListParts',
            # 'name/cos:UploadPart',
            # 'name/cos:CompleteMultipartUpload'
        ],

    }
    sts = Sts(config)
    result_dict = sts.get_credential()
    return result_dict


def check_file(bucket_name, bucket_region, key):
    secret_id = settings.COS_SECRET_ID
    secret_key = settings.COS_SECRET_KEY
    config = CosConfig(Region=bucket_region, SecretId=secret_id, SecretKey=secret_key)
    client = CosS3Client(config)
    data = client.head_object(
        Bucket=bucket_name,
        Key=key,
    )
    return data
