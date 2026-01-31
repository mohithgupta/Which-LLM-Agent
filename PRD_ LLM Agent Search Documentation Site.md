<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# PRD: LLM Agent Search Documentation Site

## 1. Project Overview

Build a documentation site for the forked `awesome-llm-apps` GitHub repository that allows users to browse and search through 100+ AI agents using their existing README.md files.

**Goal**: Create a searchable docs site with a visual homepage. Nothing more, nothing less.

## 2. Core Requirements

### 2.1 Technology Stack

- **Documentation Generator**: MkDocs with Material theme
- **Deployment**: GitHub Pages
- **Source**: Existing README.md files from agent folders (no duplication)


### 2.2 Must-Have Features

#### Homepage (`/docs/index.md`)

1. **Hero Section**
    - Site title: "Awesome LLM Apps"
    - Search bar (MkDocs built-in search)
    - Total agent count display
2. **Agent Cards Grid**
    - Display all agents as clickable cards
    - Each card shows:
        - Emoji icon (from README)
        - Agent name
        - Category badge (e.g., "Starter", "Advanced", "RAG")
        - 1-line description
        - Link to agent's README page
    - Responsive grid (3 columns desktop, 1 column mobile)
3. **Category Sections**
    - Group cards by category:
        - Starter AI Agents
        - Advanced AI Agents
        - Multi-agent Teams
        - Voice AI Agents
        - MCP AI Agents
        - RAG Agents
        - Memory Tutorials
        - Chat with X
    - Collapsible/expandable sections

#### Navigation

- Left sidebar with auto-generated navigation tree
- Categories as top-level items
- Individual agents as sub-items


#### Search

- Full-text search across all agent README files
- Search highlights in results
- Works offline (MkDocs Material built-in)


#### Agent Pages

- Each agent's README.md rendered as-is
- Preserve code blocks, images, links
- "View on GitHub" button at top linking to original folder


### 2.3 Configuration

**mkdocs.yml structure:**

```yaml
site_name: Awesome LLM Apps
site_url: https://yourusername.github.io/awesome-llm-apps
repo_url: https://github.com/yourusername/awesome-llm-apps

theme:
  name: material
  features:
    - navigation.instant
    - search.suggest
    - search.highlight
    - content.code.copy

plugins:
  - search

nav:
  - Home: index.md
  - Starter AI Agents:
    - AI Travel Agent: starter_ai_agents/ai_travel_agent.md
    - AI Blog to Podcast: starter_ai_agents/ai_blog_podcast.md
    # ... etc
  - Advanced AI Agents:
    # ...
  - RAG:
    # ...
```


### 2.4 File Structure

```
awesome-llm-apps/
├── docs/
│   ├── index.md                              # Homepage with cards
│   ├── starter_ai_agents/
│   │   ├── ai_travel_agent.md                # Symlink or copy of original README
│   │   └── ...
│   ├── advanced_ai_agents/
│   └── ...
├── mkdocs.yml                                 # Config
└── [original repo folders remain unchanged]
```


### 2.5 Automation Script

Python script to:

1. Scan all agent folders
2. Copy/symlink README.md to `docs/` with proper naming
3. Auto-generate `nav:` section in `mkdocs.yml`
4. Extract emoji + description from each README

## 3. Design Guidelines

### Visual Style

- Clean, minimal design (Material theme default)
- Emoji-first approach for visual scanning
- Card shadows on hover
- Category color coding (optional accent colors)


### Typography

- README content rendered exactly as-is
- No custom fonts (use Material defaults)


## 4. Deliverables

1. **Setup script** (`setup_docs.py`):
    - Reads repo structure
    - Generates `docs/` folder structure
    - Creates `mkdocs.yml` with navigation
    - Generates homepage `index.md` with cards
2. **Homepage template** (`docs/index.md`)
    - Cards with hardcoded/auto-generated agent list
3. **Deployment instructions**
    - One command: `mkdocs gh-deploy`
4. **README update**
    - Add "📚 Browse Docs" badge linking to GitHub Pages site

## 5. Out of Scope (DO NOT IMPLEMENT)

❌ User authentication
❌ Bookmarking/favorites
❌ Comments or ratings
❌ Analytics
❌ Dark/light mode toggle (use Material theme default)
❌ Filtering by tags beyond search
❌ Sorting options
❌ Custom JavaScript interactivity
❌ Backend/database
❌ API integration
❌ Custom styling beyond Material theme
❌ Multi-language support
❌ RSS feeds
❌ Social sharing buttons

**Rule**: If it's not listed in Section 2 (Core Requirements), don't build it.

## 6. Success Criteria

- [ ] Site deploys to GitHub Pages
- [ ] Search returns relevant agents
- [ ] All 100+ agents visible on homepage
- [ ] Clicking card opens agent's README
- [ ] Mobile responsive
- [ ] Setup takes <10 minutes for new users


## 7. Timeline

- Setup + automation: 1-2 hours
- Testing: 30 minutes
- Deployment: 5 minutes

***

**End of PRD. Build exactly this. No more, no less.**

