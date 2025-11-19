"""Contains all the data models used in inputs/outputs"""

from .campaign_create import CampaignCreate
from .campaign_create_targeting import CampaignCreateTargeting
from .clip import Clip
from .confirm_publish_request import ConfirmPublishRequest
from .error import Error
from .job import Job
from .job_params import JobParams
from .platform_rules import PlatformRules
from .platform_rules_rules import PlatformRulesRules
from .post_clips_id_variants_body import PostClipsIdVariantsBody
from .post_clips_id_variants_body_options import PostClipsIdVariantsBodyOptions
from .post_confirm_publish_response_200 import PostConfirmPublishResponse200
from .post_jobs_body import PostJobsBody
from .post_jobs_body_params import PostJobsBodyParams
from .post_rules_body import PostRulesBody
from .post_rules_body_rules import PostRulesBodyRules
from .post_upload_body import PostUploadBody
from .video_upload_response import VideoUploadResponse
from .webhook_instagram_payload import WebhookInstagramPayload
from .webhook_instagram_payload_entry_item import WebhookInstagramPayloadEntryItem

__all__ = (
    "CampaignCreate",
    "CampaignCreateTargeting",
    "Clip",
    "ConfirmPublishRequest",
    "Error",
    "Job",
    "JobParams",
    "PlatformRules",
    "PlatformRulesRules",
    "PostClipsIdVariantsBody",
    "PostClipsIdVariantsBodyOptions",
    "PostConfirmPublishResponse200",
    "PostJobsBody",
    "PostJobsBodyParams",
    "PostRulesBody",
    "PostRulesBodyRules",
    "PostUploadBody",
    "VideoUploadResponse",
    "WebhookInstagramPayload",
    "WebhookInstagramPayloadEntryItem",
)
