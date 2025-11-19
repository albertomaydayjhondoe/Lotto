/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type ConfirmPublishRequest = {
    clip_id: string;
    platform?: string;
    post_url: string;
    post_id: string;
    published_at?: string;
    confirmed_by: string;
    /**
     * Idempotency / trace id for auditing
     */
    trace_id?: string;
};

