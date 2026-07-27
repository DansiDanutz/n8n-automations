#!/usr/bin/env python3
"""Generate 10-15s product promo videos using fal.ai video models."""
import os, sys, time, json, httpx

OUTPUT_DIR = "/home/Memo1981/n8n-automations/product-videos"


def fal_headers() -> dict[str, str]:
    key = os.environ.get("FAL_KEY", "").strip()
    if not key:
        raise RuntimeError("FAL_KEY must be configured in the environment")
    return {"Authorization": f"Key {key}", "Content-Type": "application/json"}

PRODUCTS = [
    {
        "slug": "voice-ai-platform",
        "prompt": "Cinematic tech product demo: A glowing microphone icon transforms into sound waves that flow into a modern AI dashboard. Dark futuristic interface with real-time voice waveform visualization, conversation transcripts scrolling on screen, and analytics charts. Smooth camera movement, professional lighting, blue and purple neon accents. Product showcase video style.",
    },
    {
        "slug": "ai-customer-support-bot",
        "prompt": "Cinematic tech demo: A chat interface with AI bot responding to customer messages in real-time. Messages appear with smooth animations, typing indicators, satisfaction ratings pop up. Dark modern UI with green accent colors. Split screen showing customer on left, AI processing on right with neural network visualization. Professional product video.",
    },
    {
        "slug": "ai-email-assistant",
        "prompt": "Cinematic tech demo: An email inbox where AI automatically categorizes, drafts replies, and prioritizes messages. Emails flow in, get sorted by colored labels, AI writes response that types itself out. Clean modern email UI, dark theme, smooth transitions. Professional SaaS product video.",
    },
    {
        "slug": "invoice-generator-api",
        "prompt": "Cinematic tech demo: API code on left side, beautiful professional invoice being generated on right side in real-time. Numbers populate, logo appears, PDF downloads with satisfying animation. Dark code editor theme meets clean white invoice design. Professional product showcase.",
    },
    {
        "slug": "appointment-booking-system",
        "prompt": "Cinematic tech demo: A modern calendar interface where appointments get booked automatically. Time slots light up, confirmations send with smooth animations, schedule fills up. Clean white and blue UI with satisfying micro-interactions. Mobile and desktop views. Professional product video.",
    },
    {
        "slug": "ai-seo-content-generator",
        "prompt": "Cinematic tech demo: AI analyzing a website, SEO scores improving in real-time with rising graphs. Content being generated with keywords highlighted, search rankings climbing up animated charts. Dark modern dashboard with green growth indicators. Professional marketing tool video.",
    },
    {
        "slug": "social-media-auto-poster",
        "prompt": "Cinematic tech demo: Social media posts being automatically created and published across multiple platforms simultaneously. Instagram, Twitter, LinkedIn icons with posts flowing out. Content calendar filling up, engagement metrics rising. Colorful modern dashboard. Professional product video.",
    },
    {
        "slug": "webhook-relay-logger",
        "prompt": "Cinematic tech demo: Webhook events flowing through a pipeline visualization. JSON payloads streaming in real-time, getting logged with timestamps, forwarded to multiple endpoints. Matrix-style data flow with modern dark UI. Green text on dark background. Developer tool product video.",
    },
    {
        "slug": "smart-lead-nurture",
        "prompt": "Cinematic tech demo: Lead scoring dashboard with contacts moving through a sales funnel. AI analyzing leads, scores updating in real-time, automated emails triggered. CRM-style interface with pipeline visualization, warm colors. Professional B2B product video.",
    },
    {
        "slug": "api-rate-limiter",
        "prompt": "Cinematic tech demo: API traffic visualization with requests hitting a gateway. Rate limiting in action - green requests passing through, red ones being throttled. Real-time analytics dashboard showing traffic patterns, quotas, per-key usage. Dark developer tool aesthetic. Professional product video.",
    },
    {
        "slug": "ai-document-summarizer",
        "prompt": "Cinematic tech demo: Documents (PDFs, Word files) being uploaded and AI instantly generating summaries. Key points highlighted, text condensing with satisfying animation. Split view: full document on left, concise summary on right. Clean modern interface. Professional product video.",
    },
    {
        "slug": "cron-job-dashboard",
        "prompt": "Cinematic tech demo: Visual dashboard showing cron jobs executing on schedule. Timeline with jobs triggering, logs streaming, success/failure indicators. Dark monitoring dashboard with green/amber status lights, execution graphs. DevOps tool aesthetic. Professional product video.",
    },
    {
        "slug": "sports-ai",
        "prompt": "Cinematic tech demo: Sports betting analytics dashboard with live odds, arbitrage opportunities highlighted in green. Multiple sportsbook comparisons, real-time line movements, AI predictions with confidence scores. Dark theme with exciting sports imagery overlay. Professional product video.",
    },
]


def submit_video(product: dict) -> dict:
    """Submit video generation job to fal.ai."""
    # Use minimax video model (good quality, reasonable cost)
    resp = httpx.post(
        "https://queue.fal.run/fal-ai/minimax/video/01/live",
        headers=fal_headers(),
        json={"prompt": product["prompt"]},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "slug": product["slug"],
        "request_id": data["request_id"],
        "status_url": data["status_url"],
        "response_url": data["response_url"],
    }


def check_status(job: dict) -> dict:
    """Check job status."""
    resp = httpx.get(job["status_url"], headers=fal_headers(), timeout=15)
    return resp.json()


def get_result(job: dict) -> dict:
    """Get completed result."""
    resp = httpx.get(job["response_url"], headers=fal_headers(), timeout=30)
    return resp.json()


def download_video(url: str, path: str):
    """Download video file."""
    with httpx.stream("GET", url, timeout=60) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Submit all jobs
    jobs = []
    for p in PRODUCTS:
        try:
            job = submit_video(p)
            jobs.append(job)
            print(f"✅ Submitted: {p['slug']} → {job['request_id']}")
            time.sleep(1)  # Don't hammer the API
        except Exception as e:
            print(f"❌ Failed to submit {p['slug']}: {e}")

    # Save job tracking
    with open(f"{OUTPUT_DIR}/jobs.json", "w") as f:
        json.dump(jobs, f, indent=2)
    print(f"\n📋 {len(jobs)} jobs submitted. Tracking in jobs.json")

    # Poll for completion
    completed = set()
    max_wait = 600  # 10 minutes max
    start = time.time()

    while len(completed) < len(jobs) and (time.time() - start) < max_wait:
        for job in jobs:
            if job["slug"] in completed:
                continue
            try:
                status = check_status(job)
                state = status.get("status", "unknown")
                if state == "COMPLETED":
                    result = get_result(job)
                    video_url = result.get("video", {}).get("url", "")
                    if not video_url and isinstance(result.get("video"), str):
                        video_url = result["video"]
                    if not video_url:
                        # Try different response formats
                        video_url = result.get("output", {}).get("video", {}).get("url", "")
                        if not video_url:
                            video_url = result.get("url", "")

                    if video_url:
                        outpath = f"{OUTPUT_DIR}/{job['slug']}.mp4"
                        download_video(video_url, outpath)
                        size = os.path.getsize(outpath)
                        print(f"✅ Downloaded: {job['slug']}.mp4 ({size/1024:.0f}KB)")
                        completed.add(job["slug"])
                    else:
                        print(f"⚠️ {job['slug']}: completed but no video URL in response")
                        print(f"   Response keys: {list(result.keys())}")
                        completed.add(job["slug"])
                elif state == "FAILED":
                    print(f"❌ {job['slug']}: FAILED - {status.get('error', 'unknown')}")
                    completed.add(job["slug"])
                else:
                    pass  # Still processing
            except Exception as e:
                print(f"⚠️ {job['slug']}: status check error - {e}")

        if len(completed) < len(jobs):
            remaining = len(jobs) - len(completed)
            elapsed = int(time.time() - start)
            print(f"⏳ {remaining} videos still generating... ({elapsed}s elapsed)")
            time.sleep(15)

    print(f"\n🎬 Done! {len(completed)}/{len(jobs)} videos processed")
    print(f"📁 Videos saved to: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
