/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Campaign } from '../models/Campaign';
import type { CampaignCreate } from '../models/CampaignCreate';
import type { Clip } from '../models/Clip';
import type { ClipCreate } from '../models/ClipCreate';
import type { ClipVariant } from '../models/ClipVariant';
import type { ConfirmPublishRequest } from '../models/ConfirmPublishRequest';
import type { ConfirmPublishResponse } from '../models/ConfirmPublishResponse';
import type { Job } from '../models/Job';
import type { JobCreate } from '../models/JobCreate';
import type { PlatformRules } from '../models/PlatformRules';
import type { VideoUploadResponse } from '../models/VideoUploadResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class DefaultService {
    /**
     * Upload a video
     * @returns VideoUploadResponse Uploaded
     * @throws ApiError
     */
    public static postUpload({
        formData,
    }: {
        formData: {
            file?: Blob;
            metadata?: string;
        },
    }): CancelablePromise<VideoUploadResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/upload',
            formData: formData,
            mediaType: 'multipart/form-data',
        });
    }
    /**
     * Create a job
     * @returns Job Job created
     * @throws ApiError
     */
    public static postJobs({
        requestBody,
    }: {
        requestBody: JobCreate,
    }): CancelablePromise<Job> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/jobs',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * List jobs
     * @returns Job OK
     * @throws ApiError
     */
    public static getJobs(): CancelablePromise<Array<Job>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/jobs',
        });
    }
    /**
     * Get a job
     * @returns Job OK
     * @throws ApiError
     */
    public static getJobs1({
        jobId,
    }: {
        jobId: string,
    }): CancelablePromise<Job> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/jobs/{job_id}',
            path: {
                'job_id': jobId,
            },
        });
    }
    /**
     * Create a clip
     * @returns Clip Clip created
     * @throws ApiError
     */
    public static postClips({
        requestBody,
    }: {
        requestBody: ClipCreate,
    }): CancelablePromise<Clip> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/clips',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * List clip variants
     * @returns ClipVariant OK
     * @throws ApiError
     */
    public static getClipsVariants({
        clipId,
    }: {
        clipId: string,
    }): CancelablePromise<Array<ClipVariant>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/clips/{clip_id}/variants',
            path: {
                'clip_id': clipId,
            },
        });
    }
    /**
     * Confirm publish of a clip
     * @returns ConfirmPublishResponse Confirmed
     * @throws ApiError
     */
    public static postConfirmPublish({
        requestBody,
    }: {
        requestBody: ConfirmPublishRequest,
    }): CancelablePromise<ConfirmPublishResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/confirm_publish',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Instagram webhook endpoint
     * @returns any Received
     * @throws ApiError
     */
    public static postWebhookInstagram({
        requestBody,
    }: {
        requestBody: Record<string, any>,
    }): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/webhook/instagram',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Create a campaign
     * @returns Campaign Created
     * @throws ApiError
     */
    public static postCampaigns({
        requestBody,
    }: {
        requestBody: CampaignCreate,
    }): CancelablePromise<Campaign> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/campaigns',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Create platform rules
     * @returns PlatformRules Created
     * @throws ApiError
     */
    public static postRules({
        requestBody,
    }: {
        requestBody: PlatformRules,
    }): CancelablePromise<PlatformRules> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/rules',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
}
