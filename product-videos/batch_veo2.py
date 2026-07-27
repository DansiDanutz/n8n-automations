#!/usr/bin/env python3
"""Batch generate product videos using fal.ai Veo2."""
import os, time, json, httpx

OUT = "/home/Memo1981/n8n-automations/product-videos"


def fal_headers() -> dict[str, str]:
    key = os.environ.get("FAL_KEY", "").strip()
    if not key:
        raise RuntimeError("FAL_KEY must be configured in the environment")
    return {"Authorization": f"Key {key}", "Content-Type": "application/json"}

PRODUCTS = [
    ("voice-ai-platform", "Cinematic product demo video: A glowing microphone icon pulses with sound waves flowing into a modern dark-themed AI dashboard. Voice waveform visualization, conversation transcripts scrolling, analytics charts animating. Blue and purple neon accents, smooth camera movement, professional tech aesthetic."),
    ("ai-customer-support-bot", "Cinematic product demo: A modern chat interface where an AI chatbot responds instantly to customer queries. Messages appear with smooth animations, typing indicators, green checkmarks for resolved tickets. Dark themed support dashboard with real-time metrics."),
    ("ai-email-assistant", "Cinematic product demo: An email inbox where AI automatically sorts, labels, and drafts replies to incoming emails. Color-coded categories, smart prioritization arrows, auto-composed response text appearing letter by letter. Modern dark email UI."),
    ("invoice-generator-api", "Cinematic product demo: Lines of API code on left transforming into a beautiful professional invoice on right. Numbers populating, company logo appearing, total calculating, PDF generating with download animation. Clean split-screen design."),
    ("appointment-booking-system", "Cinematic product demo: A sleek calendar interface where time slots illuminate and fill with appointments. Confirmation emails send with swoosh animation, reminders pop up, daily schedule organizing itself. Clean white and blue modern UI."),
    ("ai-seo-content-generator", "Cinematic product demo: AI analyzing webpage content, SEO score gauge rising from red to green. Keywords highlighting in generated text, search ranking graphs climbing upward, organic traffic chart growing. Modern marketing dashboard."),
    ("social-media-auto-poster", "Cinematic product demo: Social media posts automatically publishing across Instagram, Twitter, LinkedIn, Facebook simultaneously. Content calendar filling with scheduled posts, engagement counters ticking up. Colorful social media dashboard."),
    ("webhook-relay-logger", "Cinematic product demo: JSON webhook payloads streaming through a pipeline visualization like The Matrix. Events being captured, logged with timestamps, forwarded to multiple endpoints. Green data streams on dark developer terminal aesthetic."),
    ("smart-lead-nurture", "Cinematic product demo: Sales leads flowing through a funnel visualization, AI scoring each lead with animated scores. Automated nurture emails triggering, pipeline stages filling. Warm CRM dashboard with conversion metrics rising."),
    ("api-rate-limiter", "Cinematic product demo: API requests visualized as particles hitting a smart gateway. Green requests flowing through, red throttled ones bouncing back. Real-time rate limit dashboard showing per-key quotas, traffic graphs. Dark developer tool."),
    ("ai-document-summarizer", "Cinematic product demo: PDF and Word documents floating in, AI scanning pages with a light beam, condensing text into bullet-point summaries. Split view: thick document shrinks to concise summary. Key insights highlighted in yellow."),
    ("cron-job-dashboard", "Cinematic product demo: Visual timeline with cron jobs triggering on schedule like a clock mechanism. Green success lights, execution logs streaming, job status cards updating. Dark DevOps monitoring dashboard aesthetic."),
    ("sports-ai", "Cinematic product demo: Live sports odds updating in real-time on a dark analytics dashboard. Arbitrage opportunities flashing green, line movement charts, AI prediction confidence meters. Multiple sportsbook comparison panels."),
]

def main():
    headers = fal_headers()
    os.makedirs(OUT, exist_ok=True)
    jobs = []

    # Submit all
    print(f"🎬 Submitting {len(PRODUCTS)} video jobs to fal.ai Veo2...\n")
    for slug, prompt in PRODUCTS:
        try:
            r = httpx.post("https://queue.fal.run/fal-ai/veo2", headers=headers,
                          json={"prompt": prompt, "duration": "8s", "aspect_ratio": "16:9"}, timeout=30)
            r.raise_for_status()
            d = r.json()
            jobs.append({"slug": slug, "rid": d["request_id"],
                        "url": f"https://queue.fal.run/fal-ai/veo2/requests/{d['request_id']}"})
            print(f"  ✅ {slug}")
            time.sleep(0.5)
        except Exception as e:
            print(f"  ❌ {slug}: {e}")

    with open(f"{OUT}/veo2_jobs.json", "w") as f:
        json.dump(jobs, f, indent=2)
    print(f"\n📋 {len(jobs)} jobs queued. Polling...\n")

    # Poll
    done = set()
    t0 = time.time()
    while len(done) < len(jobs) and (time.time() - t0) < 900:
        for j in jobs:
            if j["slug"] in done:
                continue
            try:
                r = httpx.get(j["url"], headers=headers, timeout=15)
                d = r.json()
                if "video" in d:
                    vurl = d["video"]["url"] if isinstance(d["video"], dict) else d["video"]
                    out = f"{OUT}/{j['slug']}.mp4"
                    with httpx.stream("GET", vurl, timeout=60) as dl:
                        dl.raise_for_status()
                        with open(out, "wb") as f:
                            for chunk in dl.iter_bytes():
                                f.write(chunk)
                    sz = os.path.getsize(out) / 1024
                    print(f"  ✅ {j['slug']}.mp4 ({sz:.0f}KB)")
                    done.add(j["slug"])
                elif "detail" in d and "progress" not in str(d["detail"]).lower() and "still in" not in str(d["detail"]).lower():
                    print(f"  ❌ {j['slug']}: {str(d['detail'])[:100]}")
                    done.add(j["slug"])
            except Exception as e:
                pass

        if len(done) < len(jobs):
            print(f"  ⏳ {len(done)}/{len(jobs)} done ({int(time.time()-t0)}s)")
            time.sleep(20)

    print(f"\n🎬 Complete: {len(done)}/{len(jobs)} videos")
    vids = [f for f in os.listdir(OUT) if f.endswith('.mp4') and f != 'test-veo2.mp4' and f != 'test.mp4']
    print(f"📁 {len(vids)} video files in {OUT}/")
    for v in sorted(vids):
        sz = os.path.getsize(f"{OUT}/{v}") / 1024
        print(f"  {v} ({sz:.0f}KB)")

if __name__ == "__main__":
    main()
