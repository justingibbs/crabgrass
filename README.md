# Crabgrass

An AI-powered idea capture and structuring tool. Crabgrass helps employees capture creative hunches through conversational AI, then structures them into actionable innovation proposals.

## Quick Start

### Prerequisites

- **Python 3.12+** with [uv](https://docs.astral.sh/uv/) package manager
- **Node.js 18+** with npm
- **Google AI API Key** - Get one at [Google AI Studio](https://aistudio.google.com/apikey)

### 1. Clone and Configure

```bash
git clone <repo-url>
cd crabgrass

# Copy environment template and add your API key
cp .env.example .env
# Edit .env and set GOOGLE_API_KEY=your-key-here
```

### 2. Start the Backend (Terminal 1)

```bash
cd backend
uv sync                    # Install dependencies
uv run python -m crabgrass.scripts.seed   # Seed sample data (first time only)
uv run uvicorn crabgrass.main:app --reload
```

The API will be available at `http://localhost:8000`

### 3. Start the Frontend (Terminal 2)

```bash
cd frontend
npm install                # Install dependencies
npm run dev
```

The app will be available at `http://localhost:3000`

### Sample Data

The seed script creates 4 sample ideas to demonstrate similarity search:
- **Customer Reporting Improvement** - reporting performance issues
- **Mobile App Feature Gap** - offline mode and notifications
- **Onboarding Process Streamlining** - reducing setup complexity
- **Integration with Popular Tools** - Slack, Salesforce, Zapier

These ideas have full structure (Summary, Challenge, Approach, Actions) and pre-computed embeddings for similarity matching.

---

## User Flows

### Flow 1: Capture a Quick Hunch

*Perfect for when you have a spark of an idea but don't have time to flesh it out.*

1. Open the app at `http://localhost:3000`
2. Click **"New Idea"** in the top right
3. You'll see a chat interface with a friendly AI assistant
4. Type your hunch naturally, like: *"I have an idea about using voice memos to capture employee ideas before they forget them"*
5. Press **Enter** to send
6. The AI will acknowledge your idea and may ask a clarifying question
7. Your idea is now saved! You can come back anytime to add more details.

### Flow 2: Structure an Idea with Challenge and Approach

*When you have more time to think through the problem and solution.*

1. Start a new idea or click on an existing one from the home page
2. In the chat, describe the challenge: *"The problem is that employees have great ideas during meetings but forget them by the time they get back to their desk"*
3. The AI may suggest content for the **Challenge** section - you'll see a yellow suggestion box appear on the canvas
4. Click **Accept** to add it, or **Reject** to dismiss
5. Continue the conversation: *"My approach would be to create a simple voice memo feature that transcribes and categorizes ideas automatically"*
6. Accept or refine the suggested **Approach**
7. You can also edit any section directly by clicking the **pencil icon** on the canvas

### Flow 3: Add Coherent Actions

*Break down your idea into concrete next steps.*

1. Open an existing idea
2. Scroll to the **Coherent Actions** section at the bottom of the canvas
3. Type an action in the input field: *"Research existing voice memo apps"*
4. Press **Enter** or click **+** to add it
5. Add more actions: *"Create prototype"*, *"Test with 5 employees"*
6. Click the **circle icon** to cycle through statuses:
   - Circle = Pending
   - Play icon = In Progress
   - Checkmark = Complete
7. Hover over an action and click the **trash icon** to delete it

### Flow 4: Discover Similar Ideas

*Find related ideas that might inspire collaboration or avoid duplication.*

1. Open any idea with content in the Summary, Challenge, or Approach sections
2. Look at the **Similar Ideas** panel below the chat (on the right side)
3. You'll see a list of related ideas with similarity percentages
4. Click any similar idea to navigate to it
5. When you edit your idea's content, the similar ideas automatically refresh

### Flow 5: Refine with AI Suggestions

*Let the AI help improve your idea's content.*

1. Open an existing idea
2. In the chat, ask for help: *"Can you help me write a better summary?"*
3. The AI will propose a suggestion that appears in a **yellow highlighted box** within the Summary section
4. Review the suggestion and the AI's reasoning
5. Click **Accept** to replace your current content with the suggestion
6. Or click **Reject** to dismiss and keep your original content
7. The Similar Ideas panel will refresh after accepting a suggestion

### Flow 6: Edit Directly on the Canvas

*Skip the chat and edit your idea's content directly.*

1. Open an existing idea from the home page
2. The canvas shows four sections: **Summary**, **Challenge**, **Approach**, and **Coherent Actions**
3. Hover over any section header - you'll see a **pencil icon** appear on the right
4. Click the pencil to enter edit mode
5. The section transforms into a text area with your current content
6. Make your changes - write as much or as little as you want
7. Save your changes:
   - Press **Cmd+Enter** (Mac) or **Ctrl+Enter** (Windows), or
   - Click the **green checkmark** button
8. To cancel without saving, press **Escape** or click the **red X** button
9. Your changes are saved immediately and the Similar Ideas panel refreshes

*Tip: You can mix and match - use the chat for brainstorming, then polish directly on the canvas.*

### Flow 7: Archive or Reactivate Ideas

*Keep your idea list tidy by archiving completed or paused ideas.*

1. Open the idea you want to archive
2. Notice the **status badge** next to the back button (shows "Draft", "Active", or "Archived")
3. To archive: Use the chat to say *"Please archive this idea"* or update via the API
4. Archived ideas:
   - Still appear in your ideas list (with an "Archived" badge)
   - Can still be viewed and edited
   - Won't clutter your active workspace
5. To reactivate: Open the archived idea and ask the AI *"Make this idea active again"*

*Note: Ideas start as "Draft" and become "Active" once they have substantial content.*

---

## V2 Demo Scenarios

V2 adds Objectives, Background Agents, and Surfaced Alerts. These scenarios demonstrate the new features.

### Demo Prep: Seed the Database

```bash
cd backend
uv run python -m crabgrass.scripts.seed
```

This creates:
- 4 sample ideas with full structure
- 2 top-level objectives with 4 sub-objectives
- Watches (Senior watching objectives, Sarah watching "Improve Customer Experience")
- Links between ideas and objectives
- 4 sample notifications

### Scenario 1: Bottom-Up Discovery

*ConnectionAgent discovers similar ideas across users and surfaces them.*

1. Open the app and view the **Surfaced Alerts** panel on the right
2. You should see a notification like "Found a similar idea 'Mobile App Feature Gap' (82% match)"
3. Click the notification to navigate to the related idea
4. This demonstrates how the ConnectionAgent automatically finds and surfaces connections

### Scenario 2: Objective-Linked Idea

*VP watches an objective and gets notified when ideas are linked.*

1. From the home page, click on an **Objective** in the middle column
2. Click the **Watch** button to start watching it
3. Now create a new idea: Click **New Idea** and describe something related to the objective
4. Link your idea to the objective (via the API or directly in the database for demo)
5. Check the **Surfaced Alerts** - the watcher should receive a notification

### Scenario 3: Nurturing a Nascent Idea

*NurtureAgent nudges users about nascent ideas.*

1. Create a new idea with just a title and brief summary
2. Do NOT add a Challenge or Approach (keeping it "nascent")
3. The NurtureAgent will detect this and suggest similar nascent ideas
4. Check **Surfaced Alerts** for nurture nudges like "Consider adding more detail..."

### Scenario 4: Objective Retirement Flow

*ObjectiveAgent handles orphaned ideas when objectives retire.*

1. View an objective with linked ideas
2. Click **Retire** to retire the objective
3. The ObjectiveAgent detects orphaned ideas
4. Check **Surfaced Alerts** for orphan alerts or reconnection suggestions
5. Authors of linked ideas are notified their idea is no longer linked

### Scenario 5: Real-Time Notifications

*Notifications appear in real-time via SSE.*

1. Open the app in two browser windows
2. In window 1, watch the **Surfaced Alerts** panel
3. In window 2 (or via API), create an action that triggers a notification
4. Watch the notification appear in window 1 within seconds
5. Click **Clear all** to reset notifications for the next demo

### Clearing Demo Data

To reset notifications for a fresh demo:

```bash
# Via API
curl -X DELETE http://localhost:8000/api/notifications/all

# Or delete the database and re-seed
rm data/crabgrass.duckdb
uv run python -m crabgrass.scripts.seed
```

---

## Running Tests

### Backend Tests

```bash
cd backend
uv run pytest                    # Run all tests
uv run pytest -v                 # Verbose output
uv run pytest tests/test_api/    # Run only API tests
```

### Frontend E2E Tests (Playwright)

```bash
cd frontend

# Install Playwright browsers (first time only)
npx playwright install

# Run tests
npm run test:e2e           # Headless mode
npm run test:e2e:headed    # Watch tests run in browser
npm run test:e2e:ui        # Interactive UI mode
```

### Manual Testing

See `frontend/docs/manual-test-script.md` for detailed step-by-step testing instructions with checklists.

---

## Project Structure

```
crabgrass/
├── backend/
│   ├── src/crabgrass/
│   │   ├── api/           # FastAPI endpoints
│   │   ├── agents/        # Google ADK agent & tools
│   │   ├── concepts/      # Domain models (Ideas, Summaries, etc.)
│   │   └── syncs/         # Signal-based synchronization
│   └── tests/             # pytest tests
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js pages
│   │   ├── components/    # React components
│   │   ├── hooks/         # Custom React hooks
│   │   └── lib/           # Utilities & API client
│   ├── e2e/               # Playwright E2E tests
│   └── docs/              # Documentation
└── .env.example           # Environment template
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | Yes | - | Google AI API key for Gemini LLM and embeddings |
| `DATABASE_PATH` | No | `./data/crabgrass.duckdb` | DuckDB database file path |
| `HOST` | No | `0.0.0.0` | Backend server host |
| `PORT` | No | `8000` | Backend server port |
| `FRONTEND_URL` | No | `http://localhost:3000` | Frontend URL for CORS |

---

## Architecture

Crabgrass uses a **Concepts and Synchronizations** architecture:

- **Concepts** are domain models (Idea, Summary, Challenge, Approach, CoherentAction)
- **Synchronizations** are signal-based handlers that keep data consistent (e.g., updating embeddings when content changes)
- **AG-UI Protocol** enables real-time bidirectional sync between the AI agent and the canvas UI

The AI assistant uses Google's Agent Development Kit (ADK) with tools for:
- Creating and saving ideas
- Proposing suggestions for user review
- Querying the knowledge base

---

## Troubleshooting

**Backend won't start**
- Ensure you have Python 3.12+ installed
- Check that `.env` exists with a valid `GOOGLE_API_KEY`
- Try `uv sync` to reinstall dependencies

**Frontend shows "Failed to fetch"**
- Make sure the backend is running on port 8000
- Check browser console for CORS errors
- Verify `NEXT_PUBLIC_API_URL` in `frontend/.env.local` if customized

**Similar Ideas not showing**
- Ideas need Summary/Challenge/Approach content to generate embeddings
- The first time you add content, wait a moment for embeddings to be computed

**AI responses are slow**
- This is normal for the first request as the model loads
- Subsequent requests should be faster
