from storages.backends.s3boto3 import S3Boto3Storage

__all__ = [
    "StaticStorage",
    "UploadsStorage",
]


class StaticStorage(S3Boto3Storage):
    """
    A storage class that uses the S3 storage backend for static files.
    """

    location = "static"
    file_overwrite = True


class UploadsStorage(S3Boto3Storage):
    """
    A storage class that uses the S3 storage backend for uploaded files.
    """

    location = "uploads"
    file_overwrite = False


# TODO: add a storage class that uses the S3 storage backend for signed URLs
