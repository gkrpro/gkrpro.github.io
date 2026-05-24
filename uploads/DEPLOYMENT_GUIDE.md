# Cloud Security Website — Deployment & Content Guide

## Overview
You now have a professional, static website ready to publish. Five key pages:

- **index.html** — Landing page with positioning and content overview
- **blog.html** — Blog hub with categorized posts (Governance, Frameworks, Case Studies, Leadership, Emerging Tech)
- **frameworks.html** — Portfolio of governance frameworks and implementation guides
- **decision-records.html** — Structured security decision logs with full rationale
- **about.html** — Biography and expertise overview

All files are responsive, dark-mode compatible, and optimized for readability.

---

## Quick Deploy: GitHub Pages (Free)

### Step 1: Create a GitHub Account (if you don't have one)
- Go to github.com
- Sign up with email

### Step 2: Create a Repository
1. Log into GitHub
2. Click **+** (top right) → **New repository**
3. Name it: `[your-name].github.io` (replace `[your-name]` with your actual GitHub username)
4. Keep it **Public**
5. Don't initialize with README (you'll upload your own files)
6. Click **Create repository**

### Step 3: Upload Your Files
1. In your new repository, click **Add file** → **Upload files**
2. Drag and drop all 5 HTML files:
   - index.html
   - blog.html
   - frameworks.html
   - decision-records.html
   - about.html
3. Click **Commit changes**

### Step 4: Your Site is Live
GitHub Pages automatically deploys. Your site is now live at:
```
https://[your-github-username].github.io
```

That's it. No server to maintain. No database. Pure static HTML.

---

## Custom Domain (Optional)

If you want to use your own domain (e.g., greg.cloud):

1. Buy a domain (Namecheap, GoDaddy, etc.)
2. In your GitHub repository:
   - Go to **Settings** → **Pages**
   - Under "Custom domain," enter your domain
   - Add a **CNAME** record at your domain registrar pointing to `[username].github.io`
3. GitHub handles the SSL certificate automatically

---

## How to Add New Blog Posts

Each blog post is a `<article>` block in `blog.html`. To add a new post:

### Edit blog.html:
```html
<article class="post" data-category="governance">
    <div class="post-header">
        <div class="post-meta">
            <span class="post-category">Governance</span>
            <span>Coming soon</span>
        </div>
    </div>
    <h3 class="post-title">Your Post Title</h3>
    <p class="post-excerpt">
        One or two sentences summarizing the post. This appears in the blog list.
    </p>
    <a href="#" class="read-more">Read the article →</a>
</article>
```

**What to change:**
- `data-category="governance"` — Use one of: `governance`, `frameworks`, `case-studies`, `leadership`, `emerging-tech`
- `<span>Coming soon</span>` — Change to publication date (e.g., "May 15, 2025")
- `Your Post Title` — Your actual post title
- `post-category` text — Category label (must match `data-category` name)
- `post-excerpt` — 2-3 sentence summary
- `href="#"` — Later, when you write the full post, link to it here

**How to structure the full post:**
You have two options:

**Option A: Write in a separate HTML file**
- Create `post-filename.html` (e.g., `post-three-archetype-governance.html`)
- Copy the structure from the main pages (header + nav + content + footer)
- Keep styling consistent
- Link to it from the post card in `blog.html`

**Option B: Write in Markdown, convert to HTML**
- Write in a markdown editor (free tools like HackMD.io or Markdown editor in VS Code)
- Convert to HTML (pandoc, or copy-paste into an online converter)
- Embed in a new HTML file using the same template structure

---

## Publishing Strategy

### What to publish first:
1. **Three-Archetype Governance Model** — This is your foundational framework. Write a long-form article (1500–2000 words) explaining the model, why it matters, and how to implement it.
2. **Risk-to-Traceability-to-Acceptability Decision Logic** — Your unique thinking. Document how you structure decisions to make them defensible.
3. **Multi-Cloud Control Mapping Guide** — Practical. Show how to implement the same control across Azure, AWS, GCP. Include service equivalence tables.

### Cadence:
- **Month 1:** One substantive piece (governance model)
- **Month 2:** One decision-focused piece (case study or decision record deep dive)
- **Month 3:** One tactical piece (control mapping or implementation guide)

This mix keeps the site active, positions you as both strategic and practical, and avoids the "CEO blogging rarely" trap.

---

## Customization

### Change your name:
Search for "Greg" in all files and replace with your name. Update:
- `<h1>Greg</h1>` in header
- Footer text
- Meta descriptions

### Change colors:
All colors are in the `:root` CSS variables at the top of each file. Primary color is currently:
```css
--color-primary: #0066cc; /* Blue */
--color-accent: #00a8e8;  /* Cyan */
```

Change to your preferred colors (e.g., corporate brand colors).

### Update tagline/positioning:
Edit the header subtitle in `index.html`:
```html
<p class="subtitle">Your custom positioning statement here</p>
```

### Add contact/social links:
Add to footer in all files:
```html
<footer>
    <p>&copy; 2025 Greg | Cloud Security Officer &amp; Architect</p>
    <p>
        <a href="https://linkedin.com/in/yourprofile">LinkedIn</a> • 
        <a href="https://twitter.com/yourhandle">Twitter</a> • 
        <a href="mailto:your.email@example.com">Email</a>
    </p>
</footer>
```

---

## SEO & Discoverability

### Meta tags are already set up:
Each page has:
- `<meta name="description">` — Shown in search results
- `<title>` — Browser tab title

### To improve discoverability:
1. After you publish, submit your site to Google Search Console (free)
2. Submit your sitemap (you can auto-generate one later if needed)
3. Write about topics your audience actually searches for (cloud governance, Azure security, decision frameworks)
4. Link to external resources and frameworks (NIST, CSF, SCF) to build authority

---

## Analytics (Optional)

To track traffic without collecting personal data:

### Option 1: Plausible (privacy-first, $9/month)
- Add one line to `<head>`:
```html
<script defer data-domain="yourdomain.com" src="https://plausible.io/js/script.js"></script>
```

### Option 2: Fathom Analytics (similar, privacy-first)
- Copy their tracking code into `<head>`

Avoid Google Analytics for a security/privacy angle — looks better for your positioning.

---

## Maintenance

### Monthly:
- Check for broken links
- Review analytics (what content resonates?)
- Plan next month's post

### Quarterly:
- Update decision records if new decisions are made
- Refresh frameworks if they've evolved
- Add case studies from recent work

### When you update frameworks:
- Update the frameworks.html page with new version numbers
- Add a changelog entry
- Notify your network (email, LinkedIn)

---

## What You Have

This site positions you as:
- **Pragmatic** — Frameworks are implemented, not theoretical
- **Visible** — Decision records show your thinking
- **Operationally focused** — Everything is actionable
- **Strategic** — You're thinking about leadership and organizational dynamics
- **Expert** — Multi-cloud governance, risk frameworks, decision logic

The blog filters let readers focus on what matters to them. The frameworks page is your portfolio. The decision records are your proof of judgment. The about page establishes credibility.

---

## Next Steps

1. **Deploy to GitHub Pages** (15 minutes)
2. **Customize name/colors/tagline** (10 minutes)
3. **Write your first blog post** (2–3 hours for 1500-word piece on three-archetype model)
4. **Announce it** (email + LinkedIn to your network)
5. **Repeat monthly**

---

## Questions?

Each HTML file has inline comments. All CSS is clean and readable. The structure is simple: header + nav + content + footer.

Anything you can do in a word processor, you can do here. Keep it clean, keep it substantive, and let your thinking shine through.

---

**Go publish. Make your work visible.**
