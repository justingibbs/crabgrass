# Crabgrass Manual Test Script

This document provides step-by-step instructions for manually testing the three key demo scenarios.

## Prerequisites

Before starting, ensure:

- [ ] Backend is running: `cd backend && uv run uvicorn crabgrass.main:app --reload`
- [ ] Frontend is running: `cd frontend && npm run dev`
- [ ] Database is seeded with test data (run seed script if available)
- [ ] Browser DevTools Console is open to monitor for errors

---

## Scenario 1: Capture Hunch

**Goal:** Test that a user can describe a hunch via chat and have it captured as a structured idea.

### Steps

1. **Navigate to Home Page**
   - [ ] Open `http://localhost:3000`
   - [ ] Verify the page loads with "Ideas" header
   - [ ] Verify the New Idea button/link is visible

2. **Start New Idea**
   - [ ] Click "New Idea" button
   - [ ] Verify navigation to `/ideas/new`
   - [ ] Verify chat interface appears with welcome message

3. **Describe Your Hunch**
   - [ ] Type: "I have an idea about using AI to help employees capture their creative hunches before they forget them"
   - [ ] Press Enter or click Send
   - [ ] Verify loading indicator appears

4. **Receive Agent Response**
   - [ ] Wait for agent response (may take a few seconds)
   - [ ] Verify agent acknowledges the idea
   - [ ] Verify no console errors

5. **Verify Idea Created**
   - [ ] If redirected to detail page, verify canvas sections appear
   - [ ] Verify Summary section contains content
   - [ ] Navigate back to home and verify new idea appears in list

### Expected Results
- Agent responds conversationally
- Idea is created with title and summary
- User can navigate between pages

---

## Scenario 2: Structure Idea

**Goal:** Test that a user can add Challenge and Approach via both chat and direct canvas editing.

### Steps

1. **Open Existing Idea**
   - [ ] Navigate to home page
   - [ ] Click on an existing idea
   - [ ] Verify idea detail page loads
   - [ ] Verify canvas sections are visible (Summary, Challenge, Approach, Actions)

2. **Add Challenge via Chat**
   - [ ] In the chat panel, type: "The challenge is that employees often forget their ideas before they can write them down"
   - [ ] Send the message
   - [ ] Wait for agent response
   - [ ] Verify Challenge section updates with new content

3. **Edit Summary Directly**
   - [ ] Click the Edit (pencil) icon on the Summary section
   - [ ] Verify textarea appears with current content
   - [ ] Modify the text
   - [ ] Press Cmd+Enter or click the checkmark to save
   - [ ] Verify content updates and edit mode closes

4. **Add Coherent Action**
   - [ ] Scroll to Coherent Actions section
   - [ ] Type in the "Add a new action..." input: "Research existing solutions"
   - [ ] Press Enter or click the + button
   - [ ] Verify action appears in the list

5. **Toggle Action Status**
   - [ ] Click the circle icon next to an action
   - [ ] Verify it cycles: Pending -> In Progress -> Complete
   - [ ] Verify visual indicators change (icon, strikethrough)

6. **Delete Action**
   - [ ] Hover over an action
   - [ ] Click the trash icon
   - [ ] Verify action is removed

### Expected Results
- Canvas sections are editable
- Chat messages can update canvas
- Actions can be added, toggled, and deleted
- All changes persist after page refresh

---

## Scenario 3: Discover Similar Ideas

**Goal:** Test that the Similar Ideas panel shows related ideas and updates when content changes.

### Steps

1. **Verify Similar Ideas Panel**
   - [ ] Open an existing idea
   - [ ] Locate the Similar Ideas panel (below chat)
   - [ ] Verify panel shows "Similar Ideas" header
   - [ ] Verify similar idea items are displayed (or "No similar ideas" message)

2. **Navigate to Similar Idea**
   - [ ] Click on a similar idea item
   - [ ] Verify navigation to that idea's detail page
   - [ ] Verify canvas loads with that idea's content

3. **Test Refresh on Content Change**
   - [ ] Return to original idea
   - [ ] Edit the Summary to significantly change the topic
   - [ ] Wait a moment for similar ideas to refresh
   - [ ] Verify the similar ideas list may have changed

4. **Similarity Score Display**
   - [ ] Verify each similar idea shows a similarity percentage
   - [ ] Verify ideas are ordered by similarity (highest first)

### Expected Results
- Similar ideas panel is visible and functional
- Clicking navigates to the similar idea
- Content changes trigger refresh of similar ideas
- Similarity scores are displayed

---

## Scenario 4: AI Suggestions (Accept/Reject)

**Goal:** Test that AI suggestions appear inline and can be accepted or rejected.

### Steps

1. **Trigger a Suggestion**
   - [ ] Open an existing idea or create a new one
   - [ ] In chat, ask for help with a section, e.g., "Can you suggest a better summary?"
   - [ ] Wait for agent response

2. **Verify Suggestion Appears**
   - [ ] Look for yellow-highlighted suggestion box in the relevant canvas section
   - [ ] Verify "Suggested by AI" label appears
   - [ ] Verify suggestion content is displayed
   - [ ] Verify Accept and Reject buttons are visible

3. **Accept a Suggestion**
   - [ ] Click the "Accept" button
   - [ ] Verify the section content updates with the suggestion
   - [ ] Verify the suggestion box disappears
   - [ ] Verify Similar Ideas panel refreshes

4. **Reject a Suggestion**
   - [ ] Trigger another suggestion (repeat step 1)
   - [ ] Click the "Reject" button
   - [ ] Verify the suggestion box disappears
   - [ ] Verify the original content remains unchanged

### Expected Results
- Suggestions appear inline in canvas sections
- Accepting updates the content
- Rejecting dismisses without changes
- Similar ideas refresh after accepting

---

## Error Handling Tests

### Network Error
- [ ] Stop the backend server
- [ ] Try sending a chat message
- [ ] Verify error message appears in chat
- [ ] Restart backend and verify recovery

### Invalid Idea ID
- [ ] Navigate to `/ideas/invalid-id`
- [ ] Verify error page appears
- [ ] Verify "Back to Ideas" link works

---

## Notes

- Record any bugs or unexpected behavior below
- Include screenshots if possible
- Note browser and OS version for bug reports

### Bug Reports

| Issue | Steps to Reproduce | Expected | Actual |
|-------|-------------------|----------|--------|
|       |                   |          |        |
