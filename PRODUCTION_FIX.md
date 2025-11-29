# Production Environment Fix - Authentication & Upload Issues

## Issues Identified

Based on your deployment on:
- **Frontend**: https://kalag.vercel.app  
- **Backend**: https://kalag-api.onrender.com

You're experiencing:
1. ✗ 401 errors on `/api/auth/refresh` 
2. ✗ ERR_NETWORK_CHANGED on document upload
3. ✗ "No password or email" error after login (but still able to access)

## Root Cause

**Cross-Domain Cookie Problem**: Your frontend (Vercel) and backend (Render) are on different domains. For authentication cookies to work across domains, you need specific configuration.

## Required Fixes

### 1. Backend Environment Variables (Render)

Update your environment variables on Render:

```bash
# CRITICAL: These settings allow cross-domain cookies
COOKIE_SECURE=true
COOKIE_SAMESITE=none
COOKIE_DOMAIN=  # Leave empty or don't set

# CRITICAL: Add your Vercel URL to CORS origins
CORS_ORIGINS=http://localhost:5173,https://kalag.vercel.app

# Other required variables
SECRET_KEY=your-production-secret-key-at-least-32-chars
DATABASE_URL=your-postgres-url
GOOGLE_API_KEY=your-google-api-key
QDRANT_URL=your-qdrant-url
QDRANT_API_KEY=your-qdrant-key
```

#### Why These Settings Matter:

- **`COOKIE_SECURE=true`**: Required for HTTPS (both Vercel and Render use HTTPS)
- **`COOKIE_SAMESITE=none`**: Required for cross-domain cookies (different domains)
- **`COOKIE_DOMAIN=` (empty)**: Don't set a specific domain for cross-origin
- **`CORS_ORIGINS`**: Must include your exact Vercel URL

### 2. Frontend Environment Variables (Vercel)

Update your environment variables on Vercel:

```bash
VITE_API_URL=https://kalag-api.onrender.com
```

### 3. Verify Axios Configuration

Your `frontend/src/lib/api.ts` must have:

```typescript
export const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,  // ← CRITICAL: Sends cookies cross-domain
})
```

✅ This is already correct in your code.

## Step-by-Step Deployment

### On Render (Backend):

1. Go to your Render dashboard
2. Select your Kalag API service
3. Go to **Environment** tab
4. Update/add these variables:
   ```
   COOKIE_SECURE=true
   COOKIE_SAMESITE=none
   CORS_ORIGINS=https://kalag.vercel.app
   ```
5. Click **Save Changes**
6. Render will automatically redeploy

### On Vercel (Frontend):

1. Go to your Vercel dashboard
2. Select your Kalag project
3. Go to **Settings** → **Environment Variables**
4. Verify `VITE_API_URL` is set to: `https://kalag-api.onrender.com`
5. Go to **Deployments**
6. Click **Redeploy** on latest deployment

## Testing the Fix

After redeployment:

1. **Clear your browser cookies and cache** (IMPORTANT!)
2. Go to https://kalag.vercel.app
3. Register a new account or login
4. Check browser DevTools → Network tab:
   - Login should return 200 OK
   - Cookie should be set (check Application → Cookies)
   - `/api/auth/me` should return 200 OK with user data
5. Try uploading a PDF document
6. Should see "Upload Started" and document processing

## Common Issues & Solutions

### Issue: Still getting 401 on refresh

**Solution**: Check that cookies are being set:
- Open DevTools → Application → Cookies
- Look for `refresh_token` cookie from `kalag-api.onrender.com`
- It should have: `Secure`, `HttpOnly`, `SameSite=None`

If cookie is not there:
1. Check Render logs for CORS errors
2. Verify `CORS_ORIGINS` includes exact Vercel URL (no trailing slash)
3. Make sure `withCredentials: true` in axios config

### Issue: ERR_NETWORK_CHANGED on upload

**Solution**: This is usually caused by:
1. Missing CORS headers → Check `CORS_ORIGINS` env var
2. File size too large → Check `MAX_FILE_SIZE_MB` (default 10MB)
3. Backend service sleeping (Render free tier) → Wait for cold start

### Issue: "No password or email" error but can still access

**Solution**: This is likely a validation error in the frontend. Check:
1. The `/api/auth/me` endpoint is returning correct user data
2. User data structure matches the frontend `User` interface
3. Check browser console for any parsing errors

## Code Changes Made

### 1. Fixed ID String Conversion (`backend/app/api/routes/documents.py`)

```python
# Before: current_user.id (might be UUID object)
# After: str(current_user.id) (explicit string)

user_upload_dir = os.path.join(settings.upload_dir, str(current_user.id))
```

This prevents file path errors when creating user directories.

### 2. Updated Default Cookie Settings (`backend/app/config.py`)

Changed defaults to be more flexible:
```python
cookie_secure: bool = Field(default=False)  # Override to True in production
cookie_samesite: str = Field(default="lax")  # Override to "none" in production
```

## Alternative: Same-Domain Deployment

If cross-domain cookies continue to cause issues, consider:

1. **Use Vercel for both frontend and backend**:
   - Deploy backend as Vercel serverless functions
   - Both will be on `*.vercel.app` domain

2. **Use custom domain**:
   - Set up `kalag.yourdomain.com` for frontend
   - Set up `api.yourdomain.com` for backend
   - Both on same root domain → easier cookie handling
   - Use `COOKIE_DOMAIN=.yourdomain.com`

## PDF Parsing Configuration

### LlamaParse API Key (Optional but Recommended)

For best parsing results, add your LlamaParse API key:

1. Get API key from https://cloud.llamaindex.ai/
2. Add to Render environment:
   ```
   LLAMA_CLOUD_API_KEY=llx-your-api-key-here
   ```

**Without LlamaParse**: The system will automatically fall back to PyPDF (basic text extraction, no table/chart detection).

**Common Error**: If you see `401 Unauthorized` from `llamaindex.ai` in logs:
- Your API key is invalid or missing
- The system should automatically fall back to PyPDF
- Documents will still be processed but with simpler text extraction

## Memory Issues on Render Free Tier

**Problem**: Service keeps restarting during document processing (after parsing completes).

**Cause**: Render free tier has 512MB RAM. Converting PDFs to images for vision analysis uses significant memory.

**Fixes Applied**:
1. Reduced DPI for large PDFs (100 instead of 150)
2. Limited to first 100 pages max
3. Resize images to max 2048px
4. Process pages sequentially (not parallel)
5. Free memory after each page

**If you still see restarts**:
- Upgrade to Render's Starter plan ($7/month, 512MB → 2GB RAM)
- Or use smaller PDFs (< 50 pages recommended on free tier)

## Verification Checklist

- [ ] Backend env vars updated on Render (COOKIE_SECURE, COOKIE_SAMESITE, CORS_ORIGINS)
- [ ] Frontend env vars verified on Vercel (VITE_API_URL)
- [ ] LlamaParse API key added (optional)
- [ ] Both services redeployed
- [ ] Browser cookies/cache cleared
- [ ] Can login successfully
- [ ] `/api/auth/me` returns user data (no 401)
- [ ] Can upload PDF document
- [ ] Document shows "processing" then "completed"

## Getting Help

If issues persist after following this guide:

1. Check Render logs: Dashboard → Service → Logs
2. Check browser console for errors
3. Check Network tab for failed requests
4. Verify cookie is set with correct flags
5. Test with a simple `curl` command:

```bash
# Test CORS
curl -H "Origin: https://kalag.vercel.app" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     https://kalag-api.onrender.com/api/auth/login
```

Should return CORS headers allowing the origin.

---

**Status**: Ready to deploy with these changes.
**Next**: Update environment variables and redeploy.
