Minimal TypeScript client scaffold.

This folder contains a tiny placeholder TypeScript client so tests can verify the
file layout. To regenerate using the requested tool locally, run from the repo root:

```powershell
# ensure you're in the repo root
Set-Location C:\Users\ADM\Spaytk\clients\typescript
npm init -y
npm install --save-dev openapi-typescript-codegen
npx openapi-typescript-codegen --input ..\..\openapi\orquestador_openapi.yaml --output . --client axios --useOptions
```

The scaffold here exports `OrquestadorClient` from `src/index.ts`.
