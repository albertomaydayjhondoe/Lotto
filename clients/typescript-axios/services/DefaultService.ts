/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CampaignCreate } from '../models/CampaignCreate';
import type { Clip } from '../models/Clip';
import type { ConfirmPublishRequest } from '../models/ConfirmPublishRequest';
import type { Job } from '../models/Job';
import type { PlatformRules } from '../models/PlatformRules';
import type { VideoUploadResponse } from '../models/VideoUploadResponse';
import type { WebhookInstagramPayload } from '../models/WebhookInstagramPayload';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class DefaultService {
    /**
     * Upload a full videoclip and create initial analysis job
     * @param formData
     * @returns VideoUploadResponse Uploaded
     * @throws ApiError
     */
    public static postUpload(
        formData: {
            file?: Blob;
            title?: string;
            description?: string;
            release_date?: string;
            idempotency_key?: string;
        },
    ): CancelablePromise<VideoUploadResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/upload',
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                400: `Bad request`,
            },
        });
    }
    /**
     * Create an ad-hoc job (admin/service)
     * @param requestBody
     * @returns Job Job created
     * @throws ApiError
     */
    public static postJobs(
        requestBody: {
            job_type: string;
            clip_id?: string;
            params?: Record<string, any>;
            dedup_key?: string;
        },
    ): CancelablePromise<Job> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/jobs',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * List jobs (with filters)
     * @param status
     * @param createdBy
     * @returns Job list
     * @throws ApiError
     */
    public static getJobs(
        status?: string,
        createdBy?: string,
    ): CancelablePromise<Array<Job>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/jobs',
            query: {
                'status': status,
                'created_by': createdBy,
            },
        });
    }
    /**
     * Get job status
     * @param id
     * @returns Job job
     * @throws ApiError
     */
    public static getJobs1(
        id: string,
    ): CancelablePromise<Job> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/jobs/{id}',
            path: {
                'id': id,
            },
            errors: {
                404: `not found`,
            },
        });
    }
    /**
     * List clips with filters
     * @param status
     * @param minVisualScore
     * @returns Clip clips
     * @throws ApiError
     */
    public static getClips(
        status?: string,
        minVisualScore?: number,
    ): CancelablePromise<Array<Clip>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/clips',
            query: {
                'status': status,
                'min_visual_score': minVisualScore,
            },
        });
    }
    /**
     * Request variant generation for a clip
     * @param id
     * @param requestBody
     * @returns Job variant request accepted
     * @throws ApiError
     */
    public static postClipsVariants(
        id: string,
        requestBody: {
            n_variants?: number;
            options?: Record<string, any>;
            dedup_key?: string;
        },
    ): CancelablePromise<Job> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/clips/{id}/variants',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                400: `invalid request`,
            },
        });
    }
    /**
     * Manual confirmation that a clip was published on the official account
     * @param requestBody
     * @returns any publish detected and campaign launch enqueued
     * @throws ApiError
     */
    public static postConfirmPublish(
        requestBody: ConfirmPublishRequest,
    ): CancelablePromise<{
        message?: string;
        trace_id?: string;
    }> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/confirm_publish',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                400: `bad request`,
            },
        });
    }
    /**
     * Instagram Graph webhook receiver (publication events)
     * @param requestBody
     * @returns any accepted
     * @throws ApiError
     */
    public static postWebhookInstagram(
        requestBody: WebhookInstagramPayload,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/webhook/instagram',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                400: `invalid signature`,
            },
        });
    }
    /**
     * Create/preview a campaign
     * @param requestBody
     * @returns any campaign created
     * @throws ApiError
     */
    public static postCampaigns(
        requestBody: CampaignCreate,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/campaigns',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * list campaigns
     * @returns any campaigns
     * @throws ApiError
     */
    public static getCampaigns(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/campaigns',
        });
    }
    /**
     * Get active platform rules
     * @returns PlatformRules rules
     * @throws ApiError
     */
    public static getRules(): CancelablePromise<PlatformRules> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/rules',
        });
    }
    /**
     * Propose rule changes (creates a candidate ruleset requiring approval)
     * @param requestBody
     * @returns any proposal created (awaiting approval)
     * @throws ApiError
     */
    public static postRules(
        requestBody: {
            name?: string;
            rules?: Record<string, any>;
        },
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/rules',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
}
