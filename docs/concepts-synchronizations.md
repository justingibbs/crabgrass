# Concepts and Synchronizations

Crabgrass is built on an event-driven architecture inspired by [MIT research on Concepts and Synchronizations](https://news.mit.edu/2025/mit-researchers-propose-new-model-for-legible-modular-software-1106). The core idea: complex systems should be built from independent, well-defined **concepts** connected by explicit **synchronizations**.

This document defines the MVP model for Crabgrass.

---

## Concepts

Ten independent concepts form the foundation of Crabgrass. Each has its own lifecycle and can be created, updated, and queried independently.

### Core Concepts

| Concept | Description | Key Properties |
|---------|-------------|----------------|
| **Idea** | A strategic response grouping the kernel elements. Container for Summary, Challenge, Approach, and CoherentActions. Can start as just a Summary and evolve over time. | id, title, status (Draft, Active, Archived), author, created_at, updated_at |
| **Summary** | A freeform description of the idea. The low-barrier entry point — users can capture hunches without pressure to structure them. Independent concept that belongs to one Idea. | id, content, author, created_at, updated_at |
| **Challenge** | A framing of the problem or situation. Independent concept that can be shared across multiple Ideas. | id, content, author, created_at, updated_at |
| **Approach** | The overall guiding policy chosen to address the Challenge. Independent concept that can be shared across multiple Ideas. | id, content, author, created_at, updated_at |
| **CoherentAction** | A specific step that implements the Approach. Belongs to a single Idea. | id, content, status (Pending, In Progress, Complete), author, created_at, updated_at |
| **Objective** | A desired outcome at any organizational level. Forms a flexible hierarchy where sub-objectives contribute to higher-level objectives. | id, title, description, status (Active, Retired), author, created_at, updated_at |

#### The Summary as On-Ramp

Not every idea starts fully formed. **Summary** is the freeform concept that allows users to capture early thoughts without pressure to structure them immediately. Users can jot down a hunch, a note from a meeting, or a half-formed observation.

The system respects this — but gently encourages evolution over time:

| Idea State | System Behavior |
|------------|-----------------|
| Summary only, no structure | NurtureAgent analyzes for hints of Challenge, finds similar ideas, sends gentle nudges |
| Summary + some structure | ConnectionAgent can start finding relationships |
| Full kernel + Objective link | Full system engagement — surfacing to leadership, cross-pollination |

This design acknowledges that forcing structure too early kills ideas. But structure enables the system to help. The goal is to make adding structure feel rewarding (better connections, more visibility) rather than burdensome.

### Collaboration Concepts

| Concept | Description | Key Properties |
|---------|-------------|----------------|
| **User** | A person in the system. Can author, watch, and contribute to other concepts. | id, name, email, role (Employee, Leadership) |
| **Comment** | Feedback or discussion on any concept. Lightweight mechanism for collaboration. | id, content, author, target_type, target_id, created_at |

### Agent Infrastructure Concepts

| Concept | Description | Key Properties |
|---------|-------------|----------------|
| **Session** | A stateful conversation between a human-facing agent and a user. Captures the back-and-forth dialogue. | id, agent_type, user_id, idea_id, messages[], status (Active, Archived), created_at, updated_at |
| **Notification** | An alert for a user, created by the Surfacing Agent based on events. | id, user_id, type, message, source_type, source_id, read (boolean), created_at |

---

## Relationships

Relationships connect concepts in the graph database. They fall into five categories.

### Idea Structure

| From | Relationship | To | Cardinality | Notes |
|------|--------------|-----|-------------|-------|
| Idea | HAS_SUMMARY | Summary | one-to-one | Each Idea has one Summary |
| Idea | HAS_CHALLENGE | Challenge | many-to-one | Multiple Ideas can share the same Challenge |
| Idea | HAS_APPROACH | Approach | many-to-one | Multiple Ideas can share the same Approach |
| Idea | HAS_COHERENT_ACTION | CoherentAction | one-to-many | Actions belong to a single Idea |
| Idea | ADDRESSES | Objective | many-to-many | An Idea can address multiple Objectives |
| Idea | DERIVED_FROM | Idea | many-to-one | Tracks lineage when Ideas evolve or fork |

### Objective Hierarchy

| From | Relationship | To | Cardinality | Notes |
|------|--------------|-----|-------------|-------|
| Objective | CONTRIBUTES_TO | Objective | many-to-many | Sub-objectives support higher-level Objectives |

### User Involvement

| From | Relationship | To | Cardinality | Notes |
|------|--------------|-----|-------------|-------|
| User | AUTHORED | Any concept | one-to-many | Original creator of a concept |
| User | WATCHES | Idea, Objective | many-to-many | User receives notifications for changes |
| User | CONTRIBUTED_TO | Idea | many-to-many | User has edited or added to an Idea |

### Agent-Discovered

These relationships are created by agents analyzing the graph, not by users directly.

| From | Relationship | To | Cardinality | Notes |
|------|--------------|-----|-------------|-------|
| Summary | IS_SIMILAR_TO | Summary | many-to-many | Discovered by NurtureAgent |
| Challenge | IS_SIMILAR_TO | Challenge | many-to-many | Discovered by ConnectionAgent |
| Approach | IS_SIMILAR_TO | Approach | many-to-many | Discovered by ConnectionAgent |
| Idea | IS_RELATED_TO | Idea | many-to-many | Discovered by ConnectionAgent |
| User | MAY_BE_INTERESTED_IN | Idea | many-to-many | Suggested by ConnectionAgent based on expertise |

### Supporting

| From | Relationship | To | Cardinality | Notes |
|------|--------------|-----|-------------|-------|
| Comment | ON | Any concept | many-to-one | Comments can target any concept |
| Session | FOR | Idea | many-to-one | Sessions are tied to a specific Idea |
| Notification | FOR | User | many-to-one | Notifications are delivered to a specific User |

---

## Queues

Queues decouple concept changes from agent processing. Agents subscribe to relevant queues and process items asynchronously.

| Queue | Purpose | Producers | Consumers |
|-------|---------|-----------|-----------|
| **ConnectionQueue** | Items needing relationship analysis | Idea, Challenge, Approach syncs | ConnectionAgent |
| **NurtureQueue** | Nascent Ideas needing gentle encouragement | Idea syncs (Summary-only detection) | NurtureAgent |
| **SurfacingQueue** | Items needing user notification | ConnectionAgent, NurtureAgent, AnalysisAgent, various syncs | SurfacingAgent |
| **AnalysisQueue** | Items for batch analysis | Scheduled jobs, manual triggers | AnalysisAgent |
| **ObjectiveReviewQueue** | Ideas needing review after Objective changes | Objective syncs | ObjectiveAgent |

---

## Agents

Agents are autonomous processors that react to events and perform analysis. Some are stateful (human-facing), others are stateless (batch processing).

### Human-Facing Agents (Stateful)

| Agent | Purpose | State | Inputs | Outputs |
|-------|---------|-------|--------|---------|
| **IdeaAssistantAgent** | Helps users create and edit Ideas. Guides them toward clear Challenge/Approach/Action articulation. | Session | User messages, Idea context | Idea updates, Session messages |

### Processing Agents (Stateless)

| Agent | Purpose | Inputs | Outputs |
|-------|---------|--------|---------|
| **ConnectionAgent** | Analyzes new/updated concepts to discover relationships. Finds similar Challenges, Approaches, related Ideas, and relevant Users. | ConnectionQueue items | New relationships, SurfacingQueue items |
| **NurtureAgent** | Monitors nascent Ideas (Summary only, no structure). Analyzes Summaries for hints of Challenges, finds similar Ideas, and queues gentle nudges encouraging users to evolve their Ideas. | NurtureQueue items | SurfacingQueue items (evolution suggestions, similarity findings) |
| **SurfacingAgent** | Reviews queue items and creates Notifications for relevant Users. Determines who should be alerted and how. | SurfacingQueue items | Notifications |
| **AnalysisAgent** | Conducts batch analysis to discover patterns and trends. Runs on schedule (e.g., weekly). | AnalysisQueue items, graph queries | Comments (with analysis findings), SurfacingQueue items |
| **ObjectiveAgent** | Reviews Ideas when Objectives change. When Objectives are retired, identifies orphaned Ideas and analyzes whether new or existing Objectives are relevant matches. Surfaces suggested reconnections for human review. | ObjectiveReviewQueue items, active Objectives | SurfacingQueue items (suggested reconnections, orphan alerts) |

---

## Synchronizations

Synchronizations define what happens when a concept changes. They are explicit rules connecting events to side effects.

### Idea Lifecycle

| # | Trigger | Actions |
|---|---------|---------|
| 1 | `Idea.create(ideaId)` | Add to ConnectionQueue; If Summary-only, add to NurtureQueue |
| 2 | `Idea.update(ideaId)` | Add to ConnectionQueue; If still Summary-only, add to NurtureQueue |
| 3 | `Idea.archive(ideaId)` | Add (contributors, "Idea archived") to SurfacingQueue; Archive related Sessions |
| 4 | `Idea.delete(ideaId)` | Archive related Sessions; Remove from queues |
| 5 | `Idea.linkToObjective(ideaId, objectiveId)` | Add (Objective watchers, "New Idea linked") to SurfacingQueue |
| 6 | `Idea.deriveFrom(newIdeaId, originalIdeaId)` | Create DERIVED_FROM relationship; Add (original author, "Idea derived from yours") to SurfacingQueue |
| 7 | `Idea.addStructure(ideaId)` | Remove from NurtureQueue (idea is evolving) |

### Nurturing Nascent Ideas

| # | Trigger | Actions |
|---|---------|---------|
| 8 | `NurtureAgent.analyzeSummary(ideaId)` | Parse Summary for implicit Challenge; Add (author, "We noticed a possible Challenge in your idea...") to SurfacingQueue |
| 9 | `NurtureAgent.findSimilar(ideaId)` | Find Ideas with similar Summaries; Add (author, "Your idea may relate to these...") to SurfacingQueue |
| 10 | `NurtureAgent.suggestObjective(ideaId)` | Analyze Summary against Objectives; Add (author, "This Objective might be relevant...") to SurfacingQueue |
| 11 | `NurtureAgent.gentleNudge(ideaId, daysSinceCreation)` | Periodic check; If idea still Summary-only after N days, queue encouragement to add structure |

### Kernel Elements

| # | Trigger | Actions |
|---|---------|---------|
| 12 | `Summary.create(summaryId, ideaId)` | Add Idea to NurtureQueue |
| 13 | `Summary.update(summaryId)` | Add Idea to NurtureQueue (re-analyze); Add to ConnectionQueue if Idea has structure |
| 14 | `Challenge.create(challengeId, ideaId)` | Add to ConnectionQueue (find similar Challenges) |
| 15 | `Challenge.update(challengeId)` | Add (contributors of Ideas sharing this Challenge, "Shared Challenge updated") to SurfacingQueue |
| 16 | `Approach.create(approachId, ideaId)` | Add to ConnectionQueue (find similar Approaches) |
| 17 | `Approach.update(approachId)` | Add (contributors of Ideas sharing this Approach, "Shared Approach updated") to SurfacingQueue |
| 18 | `CoherentAction.complete(actionId)` | Update parent Idea progress; Add (Idea watchers, "Action completed") to SurfacingQueue |

### Objectives

| # | Trigger | Actions |
|---|---------|---------|
| 19 | `Objective.create(objectiveId)` | Add (parent Objective watchers, "New sub-Objective created") to SurfacingQueue |
| 20 | `Objective.update(objectiveId)` | Add (watchers, "Objective updated") to SurfacingQueue |
| 21 | `Objective.retire(objectiveId)` | Add linked Ideas to ObjectiveReviewQueue; Add (watchers, "Objective retired") to SurfacingQueue |

### Collaboration

| # | Trigger | Actions |
|---|---------|---------|
| 22 | `Comment.create(commentId, targetType, targetId)` | Add (author + contributors of target, "New comment") to SurfacingQueue |
| 23 | `User.watch(userId, targetType, targetId)` | Create WATCHES relationship |
| 24 | `User.unwatch(userId, targetType, targetId)` | Remove WATCHES relationship |

### Agent Processing

| # | Trigger | Actions |
|---|---------|---------|
| 25 | `ConnectionAgent.foundSimilarity(fromId, toId, type)` | Create IS_SIMILAR_TO or IS_RELATED_TO relationship; Add to SurfacingQueue |
| 26 | `ConnectionAgent.foundRelevantUser(userId, ideaId)` | Create MAY_BE_INTERESTED_IN relationship; Add to SurfacingQueue |
| 27 | `SurfacingAgent.process(queueItem)` | Create Notification for each relevant User |
| 28 | `ObjectiveAgent.suggestReconnection(ideaId, objectiveId)` | Add (Idea contributors + Objective watchers, "Potential alignment found") to SurfacingQueue |
| 29 | `ObjectiveAgent.flagOrphan(ideaId)` | Add (Idea contributors, "Idea no longer linked to active Objective") to SurfacingQueue |
| 30 | `NurtureAgent.foundSimilarity(summaryId, similarSummaryId)` | Create IS_SIMILAR_TO relationship; Add to SurfacingQueue |
| 31 | `IdeaAssistant.sessionStart(userId, ideaId)` | Create Session |
| 32 | `IdeaAssistant.sessionEnd(sessionId)` | Archive Session |

---

## Key Use Case: Time Moves Forward

Organizations are not static. Objectives are retired, new ones emerge, and strategic priorities shift. Crabgrass must handle this gracefully — ideas that were once aligned may become orphaned, and new objectives may be relevant to existing work that no one thought to connect.

**The problem**: When an Objective is retired and new Objectives are created (e.g., during annual planning), many Ideas may suddenly lose their anchor. Without intervention, valuable work gets lost in the transition.

**The solution**: The ObjectiveAgent monitors these transitions. When Objectives are retired, it identifies orphaned Ideas and analyzes whether any new Objectives are relevant matches. Rather than requiring manual review of every Idea, the agent surfaces likely connections for human confirmation.

This is a core use case that the sync architecture must support — organizational change is constant, and the system should help navigate it rather than becoming stale.

---

## Example Flows

### Example 1: Bottom-Up Idea Discovery

**Scenario**: Sarah creates an Approach about Japan market expansion. Jim has a related Approach in a different Idea.

```
1. Sarah works with IdeaAssistantAgent
   └── Sync 21: Session.create()

2. Sarah saves her Idea with a new Approach
   └── Sync 1: Idea.create → Add to ConnectionQueue
   └── Sync 9: Approach.create → Add to ConnectionQueue

3. ConnectionAgent processes queue
   └── Finds Jim's Approach is similar
   └── Sync 18: Create IS_SIMILAR_TO relationship
   └── Add to SurfacingQueue: "Similar Approach found"

4. SurfacingAgent processes queue
   └── Sync 20: Create Notification for Sarah
   └── Sync 20: Create Notification for Jim

5. Jim sees notification, reviews Sarah's Idea
   └── Jim edits Sarah's Idea (adds to Approach)
   └── System creates CONTRIBUTED_TO relationship
   └── Sync 2: Idea.update → Add to ConnectionQueue

6. Sarah links Idea to "Expand APAC Revenue" Objective
   └── Sync 5: Add (Objective watchers) to SurfacingQueue

7. VP of Sales (watches APAC Objective) gets notified
   └── Reviews structured Idea instead of rambling email
```

### Example 2: Objectives Change, Ideas Persist

**Scenario**: During annual planning, the CEO retires the Objective "Expand into Healthcare Vertical" and creates two new Objectives: "AI-Native Product Expansion" and "Enterprise Platform Consolidation." Several Ideas were linked to the retired Objective.

```
1. CEO retires "Expand into Healthcare Vertical"
   └── Sync 14: Objective.retire
       └── Add 8 linked Ideas to ObjectiveReviewQueue
       └── Add (watchers, "Objective retired") to SurfacingQueue

2. CEO creates new Objectives
   └── Sync 12: Objective.create → Add to SurfacingQueue

3. ObjectiveAgent processes ObjectiveReviewQueue
   └── For each orphaned Idea:
       └── Analyze Challenge, Approach, Actions
       └── Compare against all active Objectives (including new ones)
       └── Score relevance to each Objective

4. ObjectiveAgent finds matches
   └── Idea "Healthcare Data Pipeline" → relevant to "Enterprise Platform Consolidation"
   └── Idea "Clinical AI Assistant" → relevant to "AI-Native Product Expansion"
   └── Idea "Hospital CRM Integration" → no strong match found

5. ObjectiveAgent queues findings
   └── Add (Idea contributors + new Objective watchers, 
       "Orphaned Idea may align with new Objective") to SurfacingQueue

6. SurfacingAgent processes queue
   └── Sync 20: Create Notifications
   └── Original Idea authors see: "Your Idea may now align with [new Objective]"
   └── New Objective watchers see: "Existing Idea may be relevant to your Objective"

7. Human review and connection
   └── Diana (original author of "Healthcare Data Pipeline") reviews suggestion
   └── Agrees with match, links Idea to "Enterprise Platform Consolidation"
   └── Sync 5: Idea.linkToObjective → notifies new Objective watchers

8. Ideas without matches
   └── "Hospital CRM Integration" remains orphaned
   └── Contributors notified: "This Idea is no longer linked to an active Objective"
   └── Idea remains searchable — may become relevant later
```

**What this enables**:
- Strategic pivots don't orphan institutional knowledge
- New Objective owners discover existing work they didn't know about
- Contributors aren't left wondering what happened to their Ideas
- The system does the tedious cross-referencing that humans skip

### Example 3: Nurturing a Nascent Idea

**Scenario**: Marcus has a hunch after a customer call but isn't ready to pitch anything. He jots down a quick note in Crabgrass.

```
1. Marcus creates an Idea with just a Summary
   └── Summary: "Customer mentioned they waste hours reconciling 
       data between our system and their ERP. Others probably have 
       this problem too. Could we build an integration?"
   └── No Challenge, no Approach, no Objective linked
   └── Sync 1: Idea.create → Add to ConnectionQueue, Add to NurtureQueue

2. NurtureAgent processes NurtureQueue
   └── Sync 8: Analyzes Summary
   └── Detects implicit Challenge: "data reconciliation pain point"
   └── Adds to SurfacingQueue: "We noticed your idea might be addressing 
       a Challenge around data integration. Want to make that explicit?"

3. Marcus ignores the nudge (busy week)
   └── Idea stays in NurtureQueue

4. NurtureAgent runs similarity check
   └── Sync 9: Finds similar Summary in another Idea
   └── Diana's Idea has Summary: "ERP integration keeps coming up in 
       customer feedback"
   └── Adds to SurfacingQueue: "Your idea may relate to Diana's — 
       you might want to compare notes"

5. Marcus sees notification, clicks through
   └── Realizes Diana is ahead of him on this
   └── Comments on Diana's Idea instead of duplicating work
   └── Archives his own Idea (captured the signal, passed it on)

   -- OR --

5. Marcus has time, evolves his Idea
   └── Adds Challenge: "Customers spend 10+ hours/week on manual 
       data reconciliation"
   └── Sync 7: Idea.addStructure → Remove from NurtureQueue
   └── Now ConnectionAgent takes over (finds similar Challenges)

6. A week later, Marcus links to Objective
   └── Links to "Improve Customer Retention"
   └── Sync 5: Objective watchers notified
   └── Idea now fully in the system — visible to leadership
```

**What this enables**:
- Low barrier to entry — capture hunches without pressure
- System gently guides toward structure (not demanding)
- Similar nascent ideas get connected early (before duplicate work)
- Users feel rewarded for adding structure (more visibility, better connections)

---

## Graph Visualization

```
[Objective: Expand APAC Revenue]
         │
         │ CONTRIBUTES_TO
         ▼
[Objective: Enter Japan Market]
         │
         │ ADDRESSES
         ▼
[Idea: Japan Partnership Strategy] ◄──CONTRIBUTED_TO── [User: Jim]
         │                          ◄──AUTHORED──────── [User: Sarah]
         │                          ◄──WATCHES───────── [User: VP Sales]
         │
         ├── HAS_CHALLENGE ──▶ [Challenge: No presence in Japan despite 15% growth]
         │
         ├── HAS_APPROACH ──▶ [Approach: Leverage APAC reseller networks]
         │                            │
         │                            └── IS_SIMILAR_TO ──▶ [Approach: APAC Channel Strategy]
         │                                                          │
         │                                                          └── (in Jim's original Idea)
         │
         ├── HAS_COHERENT_ACTION ──▶ [Action: Identify top 3 resellers]
         └── HAS_COHERENT_ACTION ──▶ [Action: Draft partnership terms]
```

---

## Implementation Notes

- **Event bus**: Synchronizations can be implemented as event handlers on a message queue (Kafka, NATS, or simpler pub/sub)
- **Graph + Vector**: All concepts should be stored in the graph database with vector embeddings for similarity search
- **Idempotency**: Syncs should be idempotent where possible — if an event is processed twice, the result is the same
- **Eventual consistency**: This is directional, not a system of record. Minor delays in sync processing are acceptable.

---

## Future Considerations (Post-MVP)

- **Automatic deduplication**: ConnectionAgent could flag likely duplicate Challenges/Approaches and suggest merging
- **Notification preferences**: Users could configure what types of changes they want to be notified about
- **Approval workflows**: Formal status transitions (Draft → Review → Active) with role-based gates
- **Analytics dashboard**: Aggregate views of where organizational energy is clustering
- **External AI integration**: Capturing and structuring outputs from ChatGPT/other tools (as shown in Company Name use case)