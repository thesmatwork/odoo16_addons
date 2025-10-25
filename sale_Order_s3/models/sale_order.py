import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import base64
import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # New fields
    order_image = fields.Binary(string="Upload Image")
    file_name = fields.Char(string="File Name")
    order_image_url = fields.Char(string="Order Image URL", readonly=True)

    def action_upload_to_s3(self):
        """Upload the image to AWS S3 and save the public URL."""
        bucket_name = "thesmatwork"   # 🔹 your bucket name
        region = "us-east-1"          # 🔹 bucket region

        for order in self:
            if not order.order_image or not order.file_name:
                raise ValueError("⚠️ Please upload an image and provide a file name.")

            try:
                # ✅ Create boto3 client (loads from ~/.aws/credentials or env vars)
                s3 = boto3.client("s3", region_name=region)

                # Decode Odoo binary field (Base64) into raw bytes
                file_content = base64.b64decode(order.order_image)

                # Upload to S3 (NO ACL, since ACLs are disabled on your bucket)
                s3.put_object(
                    Bucket=bucket_name,
                    Key=order.file_name,   # e.g. "modi.jpg"
                    Body=file_content
                )

                # ✅ Public S3 URL (works if bucket policy allows public read)
                s3_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{order.file_name}"

                # Save to Odoo field
                order.order_image_url = s3_url

                _logger.info(f"✅ Uploaded {order.file_name} to S3: {s3_url}")

            except NoCredentialsError:
                raise ValueError("❌ AWS credentials not found. Configure ~/.aws/credentials or environment variables.")
            except ClientError as e:
                raise ValueError(f"❌ Failed to upload to S3: {str(e)}")
            except Exception as e:
                raise ValueError(f"❌ Unexpected error: {str(e)}")
