# Curl examples (PowerShell friendly)

Replace `https://api.example.com` and `<TOKEN>` with your Orquestador URL and JWT/service key.

1) Upload a videoclip (multipart/form-data)

```powershell
curl -X POST "https://api.example.com/upload" \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@C:\path\to\video.mp4" \
  -F "title=My New Video" \
  -F "description=Upload for analysis" \
  -F "idempotency_key=upload-20251118-01"
```

Expected: 201 with JSON containing `video_asset_id` and `job_id`.

2) Confirm manual publish (/confirm_publish)

```powershell
curl -X POST "https://api.example.com/confirm_publish" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "clip_id": "<CLIP_UUID>",
    "platform": "instagram",
    "post_url": "https://instagram.com/p/XXXXX",
    "post_id": "1789_XXXXX",
    "published_at": "2025-11-20T10:00:00Z",
    "confirmed_by": "<ADMIN_UUID>",
    "trace_id": "trace-20251118-01"
  }'
```

Expected: 200 and `trace_id` returned; Orquestador will enqueue campaign launch workflow.
