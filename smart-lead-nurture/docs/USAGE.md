# Smart Lead Nurture - Usage Guide

## How It Works

### 1. Lead Capture
Send a POST request to the webhook with lead data:
```json
{
  "name": "Jane Smith",
  "email": "jane@techcorp.com",
  "company": "TechCorp",
  "role": "VP Engineering",
  "source": "website-form",
  "message": "Looking for automation solutions for our 50-person team"
}
```

### 2. AI Scoring
The workflow sends lead data to GPT-4o-mini which returns:
- **Score** (1-10): How qualified the lead is
- **Segment**: hot (8-10), warm (5-7), cold (1-4)
- **Reasoning**: Why this score
- **Suggested Action**: What to do next

### 3. Automated Actions

| Segment | Score | Actions |
|---------|-------|---------|
| 🔥 Hot | 8-10 | Slack alert + Priority email + CRM flag |
| 🟡 Warm | 5-7 | Nurture email sequence |
| 🔵 Cold | 1-4 | Monthly newsletter |

### 4. Customization
Edit `src/workflow.json` to:
- Change the AI scoring prompt
- Add more segments
- Connect different CRM systems
- Modify email templates
- Add SMS notifications

## Integration Examples

### With a Landing Page
```html
<form action="YOUR_WEBHOOK_URL" method="POST">
  <input name="name" required>
  <input name="email" required>
  <input name="company">
  <input name="role">
  <input type="hidden" name="source" value="landing-page">
  <textarea name="message"></textarea>
  <button type="submit">Get Started</button>
</form>
```

### With Zapier/Make
Use the webhook URL as a destination in any Zapier/Make workflow.

### With Your API
```python
import requests
requests.post("YOUR_WEBHOOK_URL", json={
    "name": "John",
    "email": "john@company.com",
    "company": "Company Inc",
    "role": "CEO",
    "source": "api",
    "message": "Need help with automation"
})
```
