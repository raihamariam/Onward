# ONWARD MASTER MEMORY VAULT

## Purpose

This is the single master source-of-truth vault for **Team Unity / Onward**. It intentionally preserves the complete information from both prior project files:

1. `CLAUDE.md` — product identity, hackathon tracks, demo scenario, product story, market/business framing, architecture, MVP, scalability, competitive defence, and Claude rules.
2. `ONWARD_SYSTEM_BUILD_MEMORY_VAULT.md` — detailed system-build architecture, engineering ownership boundaries, tech stack, n8n workflows, agent design, FastAPI decision engine, data model, infrastructure, build phases, reliability, safety, idempotency, completion gates, and deferred work.

Claude should use this vault to generate its own working `CLAUDE.md` for the repo. **Do not treat this vault as the repo instruction file itself.** It is the memory source from which the working instruction file should be derived.

## Current precedence / state

When information overlaps, use these rules:

- **Current priority is SYSTEM BUILD FIRST.** Build the real Onward system before demo/presentation work.
- Product/hackathon/demo information is still important and is preserved below for later use, but it must not distract from the current engineering phase.
- The core product truth remains: **physical incident → operational impact → feasible recovery → coordinated execution**.
- The responsibility split remains: **Claude interprets the incident; deterministic code validates operational reality; n8n orchestrates organisational action; Postgres stores system truth.**
- Primary hackathon target remains **Track 2 — Best Business Use Case & End-to-End Integration**, while preserving Track 1 originality/wow as a secondary strength.
- The initial customer/demo domain remains **university / facilities operations**, with the projector-before-a-lecture scenario as the canonical test case.
- Do not hardcode that scenario. Changing data must change the recovery result.
- Real integrations matter: Google Calendar, Slack, Gmail, Supabase/Postgres and n8n must genuinely execute/update where claimed.
- Do not add demo theatre, multi-agent complexity, extra industries, predictive maintenance, or infrastructure complexity before the core recovery loop is working end to end.

---

# SOURCE A — COMPLETE CLAUDE PROJECT BRIEF

The following section preserves the full prior `CLAUDE.md` content as source memory.

# CLAUDE.md — Team Unity / Onward

## 1. Project Identity

**Team:** Team Unity  
**Project:** Onward  
**Primary hackathon track:** Track 2 — Best Business Use Case & End-to-End Integration  
**Secondary strength:** Track 1 — Creativity & Innovation

### Core thesis

**Onward is an AI operational-response layer that turns physical-world incidents into coordinated business recovery.**

Punchy version:

> **When the physical world breaks, the business keeps moving.**

Core differentiator:

> **We don't automate fixing what broke. We automate everything that needs to happen because it broke.**

Onward is **not** an AI maintenance assistant, not a generic ticketing system, and not a photo-to-work-order demo.

The important shift is:

```text
Physical failure
→ understand the incident
→ understand what it disrupts
→ inspect real operational resources
→ generate feasible recovery options
→ human approval where needed
→ n8n coordinates real actions
→ operation continues
```

---

## 2. Why This Version Exists

The basic concept was:

```text
Photo / voice of broken equipment
→ AI diagnosis
→ n8n creates work order
→ technician assigned
```

That is too common. Existing products already cover QR fault reporting, AI-assisted diagnosis, routing, work orders, and parts suggestions.

Onward must therefore focus on **operational continuity**, not just maintenance.

Traditional maintenance asks:

> How do we repair this asset?

Onward asks:

> **What does this failure threaten, and what is the fastest safe way to preserve the operation?**

The central object is not the **work order**.

The central object is the **operation**.

---

# PART I — PRODUCT / HACKATHON STORY

## 3. Primary Demo Scenario

Use a university/facilities scenario because it is easy to understand, highly visual, and supports a complete Track 2 pipeline.

### Scenario

Time: **5:47 PM**

A lecturer enters a lecture theatre.

The projector is not working.

A class starts at **6:00 PM** with **84 students**.

### Normally

```text
Lecturer notices problem
        ↓
Emails / calls facilities
        ↓
Facilities identifies projector
        ↓
Someone checks maintenance history
        ↓
Someone checks AV technician
        ↓
Technician is not available quickly enough
        ↓
Someone looks for replacement equipment
        ↓
Someone checks another room
        ↓
Someone contacts lecturer
        ↓
Someone updates room booking
        ↓
Students eventually hear about it
```

Meanwhile, 84 people are waiting.

### With Onward

The lecturer scans the QR attached to the projector.

They say naturally:

> “Projector isn’t turning on and my lecture starts in about 10 minutes.”

They take a photo and submit.

Onward discovers:

```text
PROJECTOR AV-204
      ↓
Room 3.12
      ↓
Current fault: no power
      ↓
Maintenance history:
intermittent power issue reported 2 weeks ago
      ↓
Technician ETA: 28 minutes
      ↓
Upcoming dependency:
6:00 PM lecture
      ↓
84 attendees
      ↓
Time available: ~13 minutes
```

Onward then asks:

> **How do we preserve the lecture even though the projector failed?**

It checks alternatives.

Example:

```text
OPTION A — Wait for technician
Restore time: ~28 min
Lecture disruption: HIGH

OPTION B — Bring replacement projector
Restore time: ~21 min
Lecture disruption: HIGH

OPTION C — Move lecture to Room 2.08
Capacity: 96
Projector: operational
Available: YES
Distance: 2 minutes
Restore time: ~7 min
Lecture disruption: LOW
```

Recommendation:

> **Move the lecture to Room 2.08.**

A manager approves.

Then n8n executes real actions:

```text
APPROVED
   ↓
n8n
   ↓
├─ create maintenance work order
├─ reserve Room 2.08
├─ flag AV-204 for service
├─ update Google Calendar
├─ notify AV team in Slack
├─ email lecturer
└─ notify affected attendees
```

### Demo payoff

> **The projector is still broken. But the lecture isn’t.**

This line is central to the pitch.

---

## 4. The Impact Graph

This is Onward’s most important innovation.

Traditional maintenance:

```text
PROJECTOR
   ↓
BROKEN
   ↓
FIX PROJECTOR
```

Onward:

```text
PROJECTOR AV-204
       ↓
ROOM 3.12
       ↓
LECTURE ECON301
       ↓
6:00 PM
       ↓
84 STUDENTS
       ↓
PRESENTATION REQUIRED
       ↓
NO PROJECTOR
       ↓
SERVICE FAILURE
```

The system reasons about **business dependencies**, not only the hardware.

Other examples:

### Hotel

```text
WALK-IN FREEZER
      ↓
Restaurant
      ↓
Breakfast service
      ↓
340 guests
      ↓
Food inventory
      ↓
Safety window
```

### Warehouse

```text
FORKLIFT #17
     ↓
Loading Bay 3
     ↓
Shipment #481
     ↓
Truck departure 15:30
     ↓
Customer SLA
     ↓
$71K order
```

### Retail

```text
POS TERMINAL
     ↓
Checkout lane
     ↓
Peak traffic
     ↓
Queue capacity
     ↓
Customer experience
```

---

## 5. Hackathon Track Positioning

### Track 1 — Creativity & Innovation

Judges look for:

- originality / novelty
- wow factor
- creative tech use
- risk-taking
- storytelling
- technical feasibility

Onward is strong here because of:

- physical-world input
- multimodal AI
- the Impact Graph
- operational continuity rather than repair
- visible judge participation
- strong before → after transformation
- memorable storytelling

### Track 2 — Best Business Use Case & End-to-End Integration

Judges look for:

- clear business problem
- viable ROI
- end-to-end functionality
- integration with real systems / APIs / data
- scalability
- realistic path to production

**Primary strategy: enter Track 2.**

Do not try to optimise equally for both tracks.

The innovation should strengthen the Track 2 entry, not distract from business value.

---

## 6. Why Onward Fits Track 2

### Clear problem

A physical failure often becomes a **coordination failure** across:

- maintenance
- facilities
- inventory
- calendars
- room bookings
- staff
- communication channels
- operations

Those systems usually do not understand the consequences across one another.

### Business value

Onward reduces:

- incident-to-recovery time
- manual handoffs
- downtime
- people-hours lost
- coordination overhead

### ROI example

If 84 students lose 20 minutes:

```text
84 × 20 minutes
= 1,680 person-minutes
= 28 person-hours lost
```

If Onward reduces recovery from 28 minutes to 7 minutes:

```text
~75% reduction in incident-to-recovery time
```

Use ROI measures such as:

- minutes of downtime avoided
- person-hours protected
- number of manual handoffs removed
- recovery time reduction
- SLA / service continuity preserved

Do not invent fake financial ROI without data.

---

## 7. Real Integrations Required

Track 2 specifically rewards real integrations, not simulated UI.

At least these should genuinely work:

- **Google Calendar**
- **Slack**
- **Email**
- **Supabase / PostgreSQL**
- **n8n**

For systems we do not have access to, such as:

- CMMS
- ERP
- university room-booking software

use real Supabase tables as functional stand-ins.

Be transparent:

> “Supabase represents the facilities backend in this prototype. In deployment, that adapter connects to the organisation’s CMMS / ERP / booking system.”

Do not show fake “✓ updated” animations for actions that never happened.

---

## 8. Judge Interaction Design

We control the **world**, not the judge’s exact sentence.

The QR identifies the registered asset.

The judge / presenter can describe the symptom naturally.

Examples:

- “Screen’s dead.”
- “It won’t start.”
- “Nothing is coming on.”
- “The power button doesn’t work.”
- “The image is flickering.”

AI should map equivalent descriptions to structured incident types.

If input is too ambiguous:

> “Something is wrong.”

The system should ask a short clarification.

Do **not** depend on one scripted sentence.

---

## 9. Physical Demo

Preferred:

- small device / mini projector / monitor / printer / desk device
- attach a QR label such as `ASSET AV-204`

Fallback:

- physical asset card with:
  - image
  - asset ID
  - room
  - QR
  - status

Do not make the demo dependent on fragile hardware.

---

## 10. 4–5 Minute Demo Flow

### 0:00–0:20 — Problem

> “A projector breaks twelve minutes before a lecture. The problem isn’t just the projector. It’s the room, the lecturer, 84 students, the technician, the inventory and the schedule. Today those systems don’t understand each other.”

### 0:20–0:30 — Start live demo

> “So instead of explaining Onward, I’m going to break something.”

Scan QR.

### 0:30–1:00 — Report

Photo + natural-language / voice input.

### 1:00–1:40 — Impact

Dashboard reveals:

```text
INCIDENT
↓
ASSET
↓
FAULT
↓
EVENT
↓
84 PEOPLE
↓
12 MINUTES
```

### 1:40–2:20 — Recovery

Show feasible Plan A / B / C.

Manager / judge approves.

### 2:20–3:10 — n8n executes

Show real changes:

- Calendar
- Slack
- Email
- work order / database
- inventory / room reservation if implemented

### 3:10–3:30 — Reveal

> **“We never fixed the projector. We fixed the disruption.”**

Then:

> **“Onward is an operational reflex layer for the physical world.”**

### 3:30–4:00 — n8n proof

Show n8n for only ~10–15 seconds.

Do not spend the pitch explaining nodes.

### 4:00–4:30 — Market

University is one example.

Same architecture can later support:

- event venues
- hotels
- retail
- warehouses
- commercial facilities
- industrial operations

---

# PART II — SYSTEM ARCHITECTURE

## 11. Full System Map

This system flow must remain conceptually intact:

```text
               SOMETHING BREAKS IN REAL LIFE
                           │
                           ▼
                  QR + PHOTO + VOICE
                           │
                           ▼
                    MULTIMODAL AI
                           │
                    understands issue
                           │
                           ▼
                     ASSET DIGITAL
                        CONTEXT
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
      Manuals          History        Known faults
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                       INCIDENT
                         MODEL
                           │
                           ▼
                    IMPACT GRAPH
                           │
           "What does this break next?"
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
       Events           People          Processes
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                     RESOURCE STATE
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
     Technicians       Inventory      Alternatives
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                    RECOVERY ENGINE
                           │
                           ▼
                       PLAN A/B/C
                           │
                           ▼
                     HUMAN APPROVAL
                           │
                           ▼
                          n8n
                           │
       ┌───────────┬───────┼───────┬───────────┐
       ▼           ▼       ▼       ▼           ▼
     CMMS      Calendar  Slack   Inventory    Email
       │           │       │       │           │
       └───────────┴───────┼───────┴───────────┘
                           ▼
                  OPERATION CONTINUES
                           │
                           ▼
                    VERIFY + LEARN
```

---

## 12. Architecture Layers

### 1. Physical input

- QR / NFC / asset identifier
- photo / video
- voice / text

### 2. Incident capture UI

Simple mobile web interface.

Avoid unnecessary fields.

The user should not manually enter:

- department
- asset category
- priority
- location
- technician
- maintenance classification

AI + registered asset context should remove this friction.

### 3. Perception layer

AI handles:

- speech-to-text
- image interpretation
- symptom extraction
- incident classification
- severity
- safety risk
- ambiguity

### 4. Asset grounding

Asset identity should come primarily from the registered asset identifier.

Example:

```text
QR
 ↓
AV-204
 ↓
DATABASE
 ↓
Epson projector
Serial XYZ
Room 3.12
```

Do not ask computer vision to guess which exact corporate asset is being viewed.

Vision answers:

> What appears wrong?

Not:

> Which of our 8,000 assets is this?

### 5. Knowledge / retrieval

Ground AI with:

- manual
- maintenance history
- previous incidents
- known fault catalogue
- operational procedures
- safety rules

### 6. Impact Graph

Determine:

- what depends on this asset?
- who is affected?
- what happens next?
- how much time is available?

### 7. Resource state

Query:

- calendar
- rooms / bookings
- technicians
- technician skills
- inventory
- spare parts
- alternative assets / resources

### 8. Recovery engine

Generate feasible recovery candidates.

Reject plans that violate constraints.

Rank the valid plans.

### 9. Human approval

Use human approval for consequential changes, such as:

- moving 84 people
- spending money
- cancelling service
- high-risk or safety-related actions

### 10. n8n execution

n8n orchestrates the systems.

### 11. Verify + learn

Record:

- incident
- actions
- outcome
- asset history
- recurring failure pattern

---

## 13. AI vs Deterministic Logic

Do not use an LLM for everything.

### AI should do

- understand natural-language symptoms
- interpret images
- connect semantically similar descriptions
- extract structured symptoms
- search manuals semantically
- interpret historical notes
- classify unusual incidents
- explain recovery options
- handle ambiguous language

### Deterministic systems should do

- identify asset from QR
- read actual inventory
- check calendar availability
- check room capacity
- query technician availability
- enforce permissions
- reserve inventory
- update systems
- calculate deadlines
- execute approved actions

Example of what must **not** happen:

> “There are probably two replacement projectors available.”

Inventory must come from the actual database.

---

## 14. Structured AI Output

Never branch workflow logic on a free-form paragraph.

Use structured output.

Example:

```json
{
  "incident_type": "display_power_failure",
  "symptoms": [
    "device does not power on"
  ],
  "visual_observations": [
    "no visible physical damage"
  ],
  "severity": "high",
  "safety_risk": false,
  "confidence": 0.91,
  "likely_faults": [
    {
      "code": "POWER_SUPPLY_FAILURE",
      "confidence": 0.74
    }
  ],
  "recommended_service": "AV_SUPPORT",
  "requires_human_review": false
}
```

---

## 15. Data Model

Use **Supabase / PostgreSQL** for the hackathon.

Core tables:

| Table | Purpose |
|---|---|
| `assets` | registered physical equipment |
| `locations` | rooms / sites |
| `incidents` | every reported issue |
| `maintenance_history` | faults and repairs |
| `asset_dependencies` | what operations depend on each asset |
| `events` | classes / bookings / events |
| `technicians` | skills + availability |
| `parts` | replacement components |
| `inventory` | quantity + location |
| `alternative_resources` | alternate rooms / assets / resources |
| `work_orders` | maintenance jobs |
| `recovery_plans` | generated recovery options |
| `actions` | executed actions |
| `audit_log` | execution history |

### Critical table: `asset_dependencies`

Example:

```text
AV-204
→ ROOM-312
→ critical

ROOM-312
→ ECON301-1800
→ critical
```

This lets the system calculate downstream operational impact.

---

## 16. RAG / Knowledge Layer

Potential documents:

- AV-204 manual
- service history
- known fault catalogue
- university AV SOP
- safety policy
- replacement procedure

Flow:

```text
Manuals / docs
      ↓
Extract text
      ↓
Chunk
      ↓
Embeddings
      ↓
Vector store

Incident
   ↓
Retrieve relevant evidence
   ↓
AI triage
```

RAG supports diagnosis / context.

It does **not** invent real inventory, schedules, staff or availability.

---

## 17. Recovery Engine

Do not ask an LLM to freely decide:

> “What is the best plan?”

Use actual data to generate and validate candidates.

Example:

### Plan A — technician

```text
Technician arrival: 18:19
Event starts:       18:00

FAILED CONSTRAINT
```

### Plan B — spare projector

```text
Setup time:        19 minutes
Available time:    13 minutes

FAILED CONSTRAINT
```

### Plan C — alternate room

```text
Room:              2.08
Capacity:          96
Required:          84
Available:         YES
Transfer time:     7 minutes

VALID
```

Then rank only feasible options.

Possible prototype score:

```text
PlanScore =
0.45 × continuity
+ 0.30 × speed
+ 0.15 × cost efficiency
+ 0.10 × low disruption
```

The exact weights are not sacred.

The important principle is:

> **AI interprets. Deterministic logic verifies feasibility.**

---

## 18. n8n Workflow Architecture

Do not build one giant spaghetti workflow.

Use sub-workflows:

```text
WF-01 INCIDENT INGESTION
        ↓
WF-02 AI TRIAGE
        ↓
WF-03 OPERATIONAL IMPACT
        ↓
WF-04 RECOVERY PLANNING
        ↓
WF-05 ACTION EXECUTION
        ↓
WF-06 RESOLUTION / AUDIT
```

### WF-01 — Incident ingestion

```text
Webhook
↓
validate request
↓
load asset
↓
store media
↓
create incident
↓
trigger triage
```

### WF-02 — AI triage

```text
Photo + voice + asset context
↓
speech / vision
↓
RAG
↓
structured output
↓
confidence + safety check
```

### WF-03 — Operational impact

```text
Incident
↓
asset dependencies
↓
calendar / events
↓
people affected
↓
time constraints
↓
impact object
```

### WF-04 — Recovery planning

```text
Impact
↓
technicians
+ inventory
+ alternative resources
↓
candidate generation
↓
constraint checks
↓
ranking
↓
approval
```

### WF-05 — Action execution

```text
Approval
↓
parallel actions
├─ work order
├─ calendar
├─ inventory
├─ Slack
└─ email
```

### WF-06 — Resolution / audit

```text
Update
↓
verification
↓
close work order
↓
update asset history
↓
audit
```

---

## 19. Hackathon Tech Stack

Keep it practical.

| Layer | Choice |
|---|---|
| Mobile UI | Next.js / React PWA |
| Hosting | Vercel |
| Orchestration | n8n Cloud |
| Database | Supabase PostgreSQL |
| Media | Supabase Storage |
| Vector search | Supabase pgvector |
| Multimodal AI | Claude / Gemini / OpenAI-capable setup |
| Speech | speech-to-text API |
| Work orders | Linear / Trello / DB-backed mock CMMS |
| Messaging | Slack |
| Calendar | Google Calendar |
| Email | Gmail |
| Dashboard | Next.js + Supabase |
| Development | Claude Code |
| Source control | GitHub |

Avoid unnecessary infrastructure:

- no Kubernetes
- no Kafka
- no microservice explosion
- no multi-agent swarm just for hype

---

## 20. Safety

If the input indicates:

- sparks
- smoke
- gas
- high voltage
- medical equipment risk
- dangerous industrial machinery

do not let AI improvise repair advice.

Safety branch:

```text
safety_risk = HIGH
      ↓
do not troubleshoot automatically
      ↓
warn / isolate
      ↓
human escalation
      ↓
safety team
```

Onward automates **coordination**, not unsafe technical instructions.

---

## 21. Failure Engineering

Test:

- strange judge input
- failed image upload
- invalid model JSON
- unknown asset
- conflicting photo / voice
- low confidence
- no available room
- no technician
- no inventory
- Calendar API failure
- Slack failure
- duplicate submit
- duplicate approval
- workflow retry
- slow internet

### Idempotency

One incident must not produce duplicate actions.

Example:

```text
incident_id = INC-481
```

Retries should not create:

- five calendar bookings
- five work orders
- five emails

Use unique action keys.

---

## 22. Hackathon MVP — Must Actually Work

By submission, these seven things are the priority:

1. QR identifies a registered asset.
2. User can provide natural-language + image input.
3. AI genuinely interprets the incident.
4. System queries real asset / operational data.
5. System calculates downstream impact.
6. System dynamically generates and selects a feasible recovery option.
7. After approval, n8n visibly changes at least three real systems.

A tiny dataset is fine.

For example:

- 3 assets
- 3 rooms
- 2 technicians
- a few historical incidents
- a few alternative resources

The judges are not testing whether we built SAP.

They are testing whether the system works end to end.

---

## 23. Four-Day Build Order

### Day 1 — Skeleton

Must work:

```text
QR
→ frontend
→ n8n
→ database
→ incident created
```

Build:

- frontend
- Supabase schema
- seed data
- QR links
- n8n webhook
- incident creation

### Day 2 — Intelligence

Build:

- image analysis
- speech
- structured output
- manual retrieval / RAG
- asset history
- dependency graph
- downstream impact calculation

Must work:

```text
incident
→ event affected
→ 84 people
→ time remaining
```

### Day 3 — Action

Build:

- technician lookup
- inventory
- room lookup
- recovery candidates
- constraints
- ranking
- approval
- Slack
- Calendar
- email
- work order

Must work:

```text
approve
→ real systems change
```

### Day 4 — Win

No feature explosion.

Focus on:

- UI
- reliability
- debugging
- demo rehearsal
- fallback demo
- pitch
- Q&A defence

---

## 24. Scalability / Production Path

Initial focus:

> **University / venue facilities**

Then expand to:

```text
Universities
→ event venues
→ hotels
→ retail
→ warehouses
→ commercial facilities
→ industrial operations
```

Do not start with hospitals or heavy industry because safety and integration requirements are much higher.

Production systems can later replace the prototype adapters:

```text
Supabase facilities tables
→ real CMMS / ERP / booking connectors
```

The Onward orchestration layer remains above those systems.

---

## 25. Competitive Defence

Likely judge question:

> “Isn’t this just maintenance software?”

Answer:

> **Maintenance software optimises the repair. Onward optimises continuity.**

Normal system:

```text
asset failed
→ create ticket
→ repair
```

Onward:

```text
asset failed
→ understand operational impact
→ determine what is threatened
→ inspect available resources
→ formulate recovery
→ coordinate organisation
→ preserve the outcome
```

The question is not:

> Who can fix AV-204?

The question is:

> **What does AV-204’s failure threaten, and what is the fastest safe way to preserve that outcome?**

---

## 26. Rules for Claude While Building

### Always

- optimise for a working end-to-end Track 2 demo
- preserve the core Onward architecture
- keep n8n essential to orchestration
- use real data / real integrations wherever possible
- separate AI reasoning from deterministic facts
- use structured model outputs
- make recovery decisions data-driven
- protect idempotency
- implement human approval for consequential actions
- make failure states explicit
- favour the simplest reliable architecture

### Never

- hardcode `if projector → Room 2.08`
- fake integrations with animations
- let LLMs invent inventory / schedules / capacity
- turn the system into a generic chatbot
- add agents because “agents sound innovative”
- add infrastructure that does not improve the demo
- expand into many industries before the university scenario works
- replace Onward’s operational continuity thesis with maintenance-ticket automation
- prioritise technical complexity over visible business transformation
- add features on Day 4 unless essential

---

## 27. Success Test

The project is ready when a judge can see:

```text
Something breaks
      ↓
Onward understands it
      ↓
Onward understands what it threatens
      ↓
Onward finds a realistic way around the failure
      ↓
A human approves
      ↓
n8n coordinates real systems
      ↓
The operation continues
```

And the team can truthfully say:

> **“We never fixed the projector. We fixed the disruption.”**


---

# SOURCE B — COMPLETE SYSTEM BUILD MEMORY VAULT

The following section preserves the full prior `ONWARD_SYSTEM_BUILD_MEMORY_VAULT.md` content as source memory.

# ONWARD_SYSTEM_BUILD_MEMORY_VAULT.md

## PURPOSE OF THIS FILE

This file is the authoritative memory vault for Claude while building **Onward** for **Team Unity**.

Use this file as the project source of truth for the **SYSTEM BUILD PHASE ONLY**.

Do not drift into pitch design, stage theatrics, demo storytelling, presentation timing, animation, judge psychology, or hackathon visuals unless explicitly instructed later.

The priority right now is:

> **BUILD THE REAL END-TO-END ONWARD SYSTEM FIRST.**

Only after the core system is stable do we move to a separate demo/presentation workstream.

---

# 1. PROJECT IDENTITY

**Team:** Team Unity  
**Project:** Onward  
**Primary Hackathon Track:** Track 2 — Best Business Use Case & End-to-End Integration  
**Secondary Strength:** Track 1 — Creativity & Innovation

## Core product definition

**Onward is an AI operational-response layer that turns physical-world incidents into coordinated business recovery.**

Short product line:

> **When the physical world breaks, the business keeps moving.**

Core differentiator:

> **We don't automate fixing what broke. We automate everything that needs to happen because it broke.**

Onward is **not**:

- a generic AI maintenance assistant
- a photo-to-ticket workflow
- a technician dispatch app
- a chatbot
- an agent demo
- a work-order generator
- a CMMS replacement
- a fake hackathon animation

The system must understand:

1. what physical incident happened,
2. what registered asset is involved,
3. what that asset failure disrupts,
4. which people/events/processes are affected,
5. what operational resources are available,
6. which recovery options are actually feasible,
7. whether approval is required,
8. which real systems must change,
9. whether continuity was successfully restored.

The central object is **the operation**, not the work order.

---

# 2. CURRENT DEVELOPMENT PHASE

We are currently in:

# PHASE A — SYSTEM BUILD

The only priority is to build the actual Onward system.

Do not prioritise:

- cinematic dashboard polish
- judge interaction scripting
- pitch timing
- demo theatrics
- presentation language
- hackathon slide decks
- animations
- “wow” transitions
- stage choreography

Those belong to:

# PHASE B — DEMO + PRESENTATION

Phase B starts only after the core system reaches the engineering completion gate described later in this file.

---

# 3. SYSTEM BUILD GOAL

The final system must perform this loop:

```text
SOMETHING BREAKS IN REAL LIFE
        ↓
QR + PHOTO + VOICE
        ↓
REGISTERED ASSET IDENTIFIED
        ↓
AI UNDERSTANDS INCIDENT
        ↓
ASSET DIGITAL CONTEXT
        ↓
MANUALS + HISTORY + KNOWN FAULTS
        ↓
STRUCTURED INCIDENT MODEL
        ↓
IMPACT GRAPH
"What does this break next?"
        ↓
EVENTS + PEOPLE + PROCESSES
        ↓
RESOURCE STATE
Technicians + Inventory + Alternatives
        ↓
RECOVERY ENGINE
        ↓
PLAN A / PLAN B / PLAN C
        ↓
CONSTRAINT VALIDATION
        ↓
BEST FEASIBLE PLAN
        ↓
HUMAN APPROVAL IF REQUIRED
        ↓
n8n EXECUTION
        ↓
CALENDAR + SLACK + EMAIL + WORK ORDER + INVENTORY
        ↓
OPERATION CONTINUES
        ↓
VERIFY + AUDIT + LEARN
```

This architecture is the core of Onward.

Do not simplify it into:

```text
photo
→ AI
→ ticket
```

That would destroy the project’s differentiator.

---

# 4. PRIMARY ENGINEERING PRINCIPLE

The system responsibilities must remain separated:

## AI / Claude
AI understands **messy, ambiguous, multimodal incidents**.

## Deterministic engineering / Python
Code determines **what is actually possible**.

## n8n
n8n coordinates **what happens across the organisation**.

This division is extremely important.

In one sentence:

> **Claude interprets the incident. Python validates reality. n8n orchestrates the response.**

Never collapse these responsibilities into one LLM workflow.

---

# 5. HIGH-LEVEL ARCHITECTURE

Build this architecture:

```text
                 USER / PHYSICAL WORLD
                         │
                QR + PHOTO + VOICE
                         │
                         ▼
                NEXT.JS WEB / PWA
                         │
                         ▼
                API / INGESTION LAYER
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
      SUPABASE STORAGE          POSTGRESQL
      images / audio            incident created
             │                       │
             └───────────┬───────────┘
                         ▼
                        n8n
                 ORCHESTRATION LAYER
                         │
                         ▼
              INCIDENT INTELLIGENCE
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
         Claude        RAG       Asset context
                         │
                         ▼
              STRUCTURED INCIDENT
                         │
                         ▼
                  IMPACT ENGINE
                         │
           "What does this break next?"
                         │
                         ▼
               OPERATIONAL CONTEXT
                         │
        ┌────────────────┼─────────────────┐
        ▼                ▼                 ▼
     Events          Resources         People
     Calendar         Inventory      Technicians
                         │
                         ▼
                RECOVERY ENGINE
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
            Plan A     Plan B     Plan C
                         │
                         ▼
              CONSTRAINT VALIDATION
                         │
                         ▼
                  BEST VALID PLAN
                         │
                         ▼
                   APPROVAL GATE
                         │
                         ▼
                        n8n
                         │
       ┌─────────┬───────┼───────┬─────────┐
       ▼         ▼       ▼       ▼         ▼
   Calendar    Slack   Email    Work     Inventory
                              Order
                         │
                         ▼
                 AUDIT + RESOLUTION
```

---

# 6. LOCKED TECH STACK

Keep the stack intentionally small and practical.

| Layer | Technology | Responsibility |
|---|---|---|
| Frontend | Next.js + TypeScript | mobile incident UI + operations UI |
| Hosting | Vercel | frontend deployment |
| Orchestration | n8n Cloud | workflow coordination |
| Database | Supabase PostgreSQL | core operational data |
| File storage | Supabase Storage | photos, audio, manuals |
| Vector retrieval | Supabase pgvector | manual/history semantic retrieval |
| AI reasoning | Claude | multimodal incident intelligence |
| Development assistant | Claude Code | implementation, testing, debugging |
| Deterministic engineering service | Python + FastAPI | impact + recovery logic |
| Backend hosting | Railway or Render | FastAPI deployment |
| Calendar integration | Google Calendar | real booking/update integration |
| Messaging | Slack | real team notification |
| Email | Gmail | real notification integration |
| Source control | GitHub | repository + version history |
| Monitoring | n8n execution logs + app logs | hackathon-level observability |

Core system components:

```text
Next.js
n8n
FastAPI
Supabase
```

Everything else is an integration.

---

# 7. WHAT NOT TO ADD

Do not add infrastructure just because it looks sophisticated.

Do not build:

- Kubernetes
- Kafka
- RabbitMQ
- complex event buses
- Redis unless forced by a real technical need
- dozens of microservices
- multi-agent swarms
- service mesh
- distributed orchestration layers
- enterprise observability stacks
- excessive cloud complexity

Hackathon value comes from a strong end-to-end system, not infrastructure theatre.

---

# 8. AI / AGENT ARCHITECTURE

Do not build a multi-agent architecture.

Use one tightly controlled AI intelligence component:

# Incident Intelligence Agent

Its purpose is only:

```text
INPUT
- photo
- voice or text
- registered asset context
- maintenance history
- retrieved manual sections
- known fault context

        ↓

AI INTERPRETATION

        ↓

STRUCTURED INCIDENT JSON
```

AI responsibilities:

- understand natural-language symptom descriptions
- interpret photos
- connect semantically similar wording
- extract symptoms
- classify incident type
- estimate severity
- detect safety risk
- identify likely fault categories
- identify required service capability
- explain incident meaning
- handle ambiguity
- request clarification when necessary

AI must **not** invent:

- inventory
- room availability
- technician availability
- booking capacity
- event times
- costs
- authorisation
- part quantities
- staff schedules
- deadlines

Those facts must come from deterministic systems and database queries.

---

# 9. STRUCTURED AI OUTPUT CONTRACT

Never allow downstream logic to depend on free-form prose.

Claude must return validated structured data.

Example:

```json
{
  "incident_type": "power_failure",
  "symptoms": [
    "projector does not power on"
  ],
  "visual_observations": [
    "no visible physical damage"
  ],
  "severity": "high",
  "safety_risk": false,
  "confidence": 0.91,
  "likely_faults": [
    {
      "code": "POWER_SUPPLY_FAILURE",
      "confidence": 0.74
    }
  ],
  "required_capability": "AV_SUPPORT",
  "requires_human_review": false
}
```

The schema must be validated before the workflow continues.

Low-confidence results must trigger clarification or review rather than confident automation.

---

# 10. n8n ROLE

n8n is the **central nervous system**.

n8n is not:

- the database
- the decision engine
- the business logic engine
- the AI model
- the UI

n8n coordinates the system.

Build six modular workflows.

---

# 11. n8n WORKFLOW ARCHITECTURE

## WF-01 — INCIDENT INTAKE

Responsibility:

- receive incident
- validate request
- resolve registered asset
- store media
- create incident
- trigger intelligence workflow

Flow:

```text
Webhook
↓
Validate request
↓
Find asset
↓
Create incident
↓
Store attachments
↓
Call WF-02
```

Exit condition:

A valid incident record exists and references a registered asset.

---

## WF-02 — INCIDENT INTELLIGENCE

Responsibility:

- retrieve context
- run multimodal AI
- use RAG where necessary
- validate structured incident output
- enforce confidence / safety checks

Flow:

```text
Incident
+
Asset context
+
Photo
+
Voice / text
↓
Retrieve manual/history context
↓
Claude
↓
Structured parser
↓
Schema validation
↓
Confidence check
↓
Safety check
↓
Call WF-03
```

Exit condition:

A valid structured incident object exists.

---

## WF-03 — OPERATIONAL IMPACT

Responsibility:

- understand downstream effects
- traverse asset dependencies
- identify event/process impact
- calculate urgency

Flow:

```text
Incident
↓
Asset dependencies
↓
Location
↓
Calendar / Events
↓
People affected
↓
Process dependencies
↓
Time constraints
↓
Impact object
↓
Call WF-04
```

Example expected result:

```json
{
  "affected_event": "ECON301",
  "people_affected": 84,
  "minutes_until_event": 13,
  "criticality": "high",
  "service_at_risk": "lecture delivery"
}
```

---

## WF-04 — RECOVERY PLANNING

Responsibility:

- query real resources
- generate possible recovery paths
- call deterministic recovery engine
- reject infeasible plans
- rank valid plans
- route to approval if required

Flow:

```text
Impact object
↓
Query:
- technicians
- rooms
- inventory
- replacement assets
- schedules
↓
FastAPI Recovery Engine
↓
Candidate Plan A / B / C
↓
Constraint validation
↓
Rank feasible plans
↓
Approval gate
```

Exit condition:

A recommended feasible recovery plan exists.

---

## WF-05 — RECOVERY EXECUTION

Responsibility:

Execute the approved recovery plan.

Flow:

```text
Approved plan
↓
Parallel actions
├─ Google Calendar
├─ Slack
├─ Gmail
├─ work_orders
├─ inventory
└─ room / resource reservation
```

Every action must return a success/failure result.

Exit condition:

The approved plan has been executed or safely failed.

---

## WF-06 — RESOLUTION & AUDIT

Responsibility:

- consolidate execution results
- update incident
- update asset history
- record actions
- create audit trail
- mark recovery status

Flow:

```text
Execution results
↓
Update incident
↓
Update asset history
↓
Write actions
↓
Write audit log
↓
Mark recovery status
```

Exit condition:

The incident has a traceable final state.

---

# 12. FASTAPI ENGINEERING SERVICE

Do not bury deterministic engineering logic inside n8n.

Create one small Python FastAPI service.

Main modules:

```text
services/decision-engine/
├── impact/
├── recovery/
├── constraints/
├── scoring/
└── tests/
```

Two primary responsibilities:

## Impact Engine

Input example:

```json
{
  "asset_id": "AV-204",
  "incident_type": "power_failure",
  "timestamp": "..."
}
```

Output example:

```json
{
  "affected_event": "ECON301",
  "people_affected": 84,
  "deadline_minutes": 13,
  "criticality": "high"
}
```

---

## Recovery Engine

Inputs:

```text
incident
impact
rooms
technicians
inventory
replacement assets
constraints
```

Responsibilities:

- generate candidate recovery plans
- evaluate feasibility
- reject invalid plans
- rank valid plans
- explain why plans pass/fail

The engine must not blindly ask an LLM what to do.

---

# 13. RECOVERY ENGINE EXAMPLE

Technician option:

```text
Technician ETA = 28 minutes
Available time = 13 minutes

28 > 13

RESULT: INVALID
```

Replacement projector:

```text
Pickup + setup time = 19 minutes
Available time = 13 minutes

19 > 13

RESULT: INVALID
```

Alternative room:

```text
Capacity = 96
Required = 84
96 >= 84
PASS

Available = true
PASS

Projector operational = true
PASS

Transfer time = 7 minutes
Available time = 13 minutes
7 <= 13
PASS

RESULT: VALID
```

Room 2.08 should only win because real data and constraints make it the best option.

Never hardcode:

```text
if projector_failed:
    choose Room 2.08
```

---

# 14. RECOVERY SCORING

Prototype scoring may use:

```text
PlanScore =
0.45 × continuity
+ 0.30 × speed
+ 0.15 × cost efficiency
+ 0.10 × low disruption
```

The exact weights are not sacred.

The core principle is:

> Generate feasible plans from actual system state, then rank them.

Never rank an impossible plan above a valid plan.

Constraint checking comes before scoring.

---

# 15. DATABASE DESIGN

Use Supabase PostgreSQL.

Start with only the core tables.

| Table | Purpose |
|---|---|
| `assets` | registered physical equipment |
| `locations` | rooms/sites |
| `incidents` | reported failures |
| `maintenance_history` | previous failures and repairs |
| `dependencies` | asset → operation relationships |
| `events` | classes / bookings |
| `technicians` | staff skills + availability |
| `inventory` | parts / replacement assets |
| `resources` | alternate rooms / assets |
| `recovery_plans` | candidate recovery plans |
| `work_orders` | maintenance actions |
| `actions` | executed actions |
| `audit_log` | system activity history |

---

# 16. MOST IMPORTANT TABLE: DEPENDENCIES

This table creates the core Onward advantage.

Example:

```text
AV-204
↓
ROOM-312

ROOM-312
↓
ECON301

ECON301
↓
84 attendees
```

Conceptually:

```text
source_type
source_id
dependency_type
dependency_id
importance
required_for_operation
```

The Impact Engine traverses these relationships.

This is what transforms:

```text
broken projector
```

into:

```text
84-person lecture at risk in 13 minutes
```

---

# 17. RAG / KNOWLEDGE LAYER

Use Supabase pgvector.

Potential knowledge sources:

- AV-204 manual
- maintenance history
- known fault catalogue
- university AV procedures
- safety procedures
- replacement instructions

Flow:

```text
manuals / documents
↓
extract text
↓
chunk
↓
embeddings
↓
pgvector
```

At runtime:

```text
incident symptoms
↓
semantic query
↓
retrieve relevant evidence
↓
Claude interpretation
```

RAG supports incident understanding.

RAG must never be used as the source of truth for:

- inventory
- room availability
- technician schedules
- event calendars
- actual business state

---

# 18. INFRASTRUCTURE TOPOLOGY

Keep infrastructure simple.

```text
                         INTERNET

                ┌──────────────────┐
                │      VERCEL      │
                │    Next.js UI    │
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │     n8n Cloud    │
                │  orchestration   │
                └───────┬──────────┘
                        │
           ┌────────────┼─────────────┐
           ▼            ▼             ▼

       SUPABASE      FASTAPI       CLAUDE API

       Postgres     Impact /       incident
       Storage      Recovery       intelligence
       pgvector     Engine
```

n8n also connects to:

```text
Google Calendar
Slack
Gmail
```

---

# 19. REPOSITORY STRUCTURE

Use this structure:

```text
onward/
│
├── apps/
│   └── web/
│       ├── app/
│       ├── components/
│       ├── api/
│       └── lib/
│
├── services/
│   └── decision-engine/
│       ├── app/
│       │   ├── impact/
│       │   ├── recovery/
│       │   ├── constraints/
│       │   └── scoring/
│       └── tests/
│
├── database/
│   ├── migrations/
│   ├── seed/
│   └── schema.sql
│
├── n8n/
│   ├── wf01-incident-intake.json
│   ├── wf02-ai-triage.json
│   ├── wf03-impact.json
│   ├── wf04-recovery.json
│   ├── wf05-execution.json
│   └── wf06-resolution.json
│
├── knowledge/
│   ├── manuals/
│   ├── procedures/
│   └── safety/
│
├── tests/
│
├── CLAUDE.md
├── ONWARD_SYSTEM_BUILD_MEMORY_VAULT.md
└── README.md
```

---

# 20. BUILD ORDER — DO NOT SKIP PHASES

The build order is locked.

| Phase | Build | Exit condition |
|---|---|---|
| 0 | Repo + environments | everything deploys |
| 1 | Database | seeded university world exists |
| 2 | Incident intake | QR → incident row works |
| 3 | AI intelligence | image/text → structured incident works |
| 4 | Impact Graph | asset → affected operation works |
| 5 | Recovery Engine | viable recovery is calculated dynamically |
| 6 | n8n orchestration | end-to-end workflow executes |
| 7 | Real integrations | Slack/Calendar/Email actually change |
| 8 | Approval | consequential actions pause correctly |
| 9 | Reliability | failures/retries/duplicates handled |
| 10 | UI | system is usable |
| 11 | Testing | end-to-end system passes |

Do not start demo work before Phase 11 completion or explicit instruction.

---

# 21. PHASE 0 — REPO + ENVIRONMENT

Create:

- GitHub repository
- Next.js app
- FastAPI service
- Supabase project
- n8n Cloud workspace
- environment-variable strategy
- deployment targets
- local development setup

Success condition:

- web app deploys
- FastAPI health endpoint works
- Supabase connects
- n8n can call both
- secrets are not committed

---

# 22. PHASE 1 — DATABASE

Build schema and seed a small university world.

Minimum useful dataset:

- 3 assets
- 3 rooms
- 2 technicians
- 1–3 events
- maintenance history
- some inventory
- alternate resources
- dependency relationships

Example:

```text
Asset AV-204
Room 3.12
ECON301
84 attendees
start time 18:00
```

Success condition:

The system has enough real relational data to support impact and recovery calculations.

---

# 23. PHASE 2 — INCIDENT INTAKE

First major milestone:

```text
QR
↓
asset loaded
↓
incident submitted
↓
Supabase incident created
↓
n8n triggered
↓
system sees incident
```

Do not proceed until this works reliably.

---

# 24. PHASE 3 — AI INCIDENT INTELLIGENCE

Second major milestone:

```text
QR
↓
photo + description
↓
Claude
↓
structured incident JSON
↓
schema validation
↓
incident intelligence stored
```

The system should differentiate:

- no power
- flickering image
- connection problem
- physical damage
- safety hazard

Success condition:

Natural-language and image input produces reliable structured incident data.

---

# 25. PHASE 4 — IMPACT GRAPH

This is the heart of Onward.

Do not continue until this works dynamically.

Required transformation:

```text
AV-204 failed
↓
Room 3.12 affected
↓
ECON301 affected
↓
84 people affected
↓
event starts in 13 minutes
```

Changing dependencies or event data must change the output.

Success condition:

The impact result comes from data relationships, not hardcoded scenario logic.

---

# 26. PHASE 5 — RECOVERY ENGINE

Input:

```text
incident
+
impact
+
resource state
```

Output:

```text
Plan A
Plan B
Plan C
↓
constraint evaluation
↓
valid options
↓
ranked recommendation
```

Dynamic behaviour is mandatory.

Examples:

If:

```text
Room 2.08 available = false
```

another plan must win.

If:

```text
technician ETA = 5 minutes
```

technician repair may become best.

Success condition:

The recommendation changes correctly when operational data changes.

---

# 27. PHASE 6 — n8n ORCHESTRATION

Connect all core modules:

```text
Incident intake
↓
AI intelligence
↓
Impact
↓
Recovery
↓
Approval
↓
Execution
↓
Audit
```

Success condition:

One incident can flow through the entire n8n orchestration chain.

---

# 28. PHASE 7 — REAL INTEGRATIONS

At minimum, make these genuinely real:

- Google Calendar
- Slack
- Gmail
- Supabase updates

Do not fake the result.

If Onward says:

```text
Calendar updated
```

the calendar must actually be updated.

If it says:

```text
Slack notified
```

a real Slack message must exist.

If it says:

```text
Email sent
```

the email must genuinely be sent.

This is crucial for Track 2 judging.

---

# 29. PHASE 8 — APPROVAL + SAFETY

Consequential actions must pause for approval.

Examples:

- moving 84 people to another room
- spending money
- cancelling or moving an event
- changing operational resources

Approval options:

```text
APPROVE
REJECT
CHOOSE OTHER
```

Low-confidence or high-risk incidents should escalate.

---

# 30. PHASE 9 — RELIABILITY

Before demo work, explicitly test:

```text
happy path
low-confidence AI path
unsafe incident path
no recovery available path
duplicate request path
API failure path
approval rejection path
retry path
```

---

# 31. IDEMPOTENCY

Every workflow action needs a unique identity.

Example:

```text
incident_id = INC-481
```

Action key example:

```text
INC-481:calendar:reserve-room-208
```

Retries must not produce:

- duplicate room reservations
- duplicate calendar events
- duplicate emails
- duplicate work orders
- duplicate Slack notifications

Idempotency is required.

---

# 32. SAFETY ENGINEERING

If the system detects:

- sparks
- smoke
- gas
- high voltage
- dangerous machinery
- medical equipment risk
- other safety-critical situations

do not generate casual repair instructions.

Safety path:

```text
safety_risk = HIGH
↓
do not troubleshoot automatically
↓
warn / isolate
↓
human escalation
↓
safety team
```

Onward automates coordination, not dangerous repair advice.

---

# 33. FIRST PRIORITY MILESTONE

Before RAG sophistication, UI polish, or recovery intelligence:

```text
QR
↓
asset loaded
↓
report incident
↓
Supabase row created
↓
n8n triggered
↓
system acknowledges incident
```

If this is not reliable, stop and fix it.

---

# 34. SECOND PRIORITY MILESTONE

Then:

```text
photo + natural-language description
↓
Claude
↓
structured incident output
↓
validated + stored
```

---

# 35. THIRD PRIORITY MILESTONE

Then:

```text
incident
↓
dependencies
↓
affected operation
↓
people affected
↓
deadline
```

This is the Onward differentiator.

---

# 36. FOURTH PRIORITY MILESTONE

Then:

```text
incident + impact + resources
↓
candidate recoveries
↓
constraint validation
↓
best feasible plan
```

---

# 37. FIFTH PRIORITY MILESTONE

Then:

```text
approved plan
↓
n8n
↓
real calendar change
real Slack notification
real email
real database work order
```

---

# 38. ENGINEERING COMPLETION GATE

Do not move to demo/presentation phase until the following exist:

- [ ] registered asset lookup works
- [ ] incident submission works
- [ ] multimodal incident intelligence works
- [ ] structured output validation works
- [ ] asset dependencies work
- [ ] downstream impact calculation works
- [ ] resource queries work
- [ ] recovery candidates are dynamic
- [ ] constraint validation works
- [ ] recommendation changes when data changes
- [ ] approval gate works
- [ ] n8n execution works
- [ ] Google Calendar integration works
- [ ] Slack integration works
- [ ] Gmail integration works
- [ ] Supabase updates work
- [ ] audit logging exists
- [ ] duplicate requests are safe
- [ ] retry path exists
- [ ] unsafe incident path exists
- [ ] no-recovery path exists
- [ ] end-to-end test passes

Only then is the **core system complete**.

---

# 39. BUILD STRATEGY FOR CLAUDE CODE

Claude Code should work one module at a time.

Do not ask:

> Build Onward.

Instead proceed:

```text
Architecture
↓
Database
↓
Incident API
↓
n8n intake
↓
AI schema
↓
AI integration
↓
Impact engine
↓
Recovery engine
↓
n8n orchestration
↓
Real integrations
↓
Approval
↓
Reliability
↓
Tests
```

For every module:

1. inspect existing repository state,
2. state what needs to change,
3. implement,
4. run tests,
5. verify behaviour,
6. show evidence,
7. fix failures,
8. commit,
9. only then continue.

No giant speculative code dump.

---

# 40. CLAUDE BUILD RULES

## ALWAYS

- preserve the Onward architecture
- optimise for end-to-end Track 2 functionality
- keep n8n central to orchestration
- keep deterministic business facts outside the LLM
- use real database state
- use structured AI outputs
- validate AI output
- make recovery dynamic
- use constraints before scoring
- implement approval for consequential changes
- keep modules testable
- write tests
- add logs
- preserve idempotency
- expose failure states
- use the smallest architecture that works
- use real integrations wherever possible
- favour reliability over cleverness

---

## NEVER

- hardcode `projector → Room 2.08`
- hardcode the judge scenario
- fake integrations
- let AI invent inventory
- let AI invent room capacity
- let AI invent schedules
- let AI invent technician availability
- let AI invent event timing
- let AI perform unsafe repair reasoning
- build multi-agent systems without a real need
- add infrastructure for appearance
- create one giant n8n spaghetti workflow
- over-focus on frontend visuals
- add predictive maintenance now
- build for multiple industries now
- start demo design before the system works
- confuse maintenance automation with operational continuity

---

# 41. FEATURES EXPLICITLY DEFERRED

Do not build yet:

- predictive maintenance
- IoT telemetry
- NFC
- RFID
- BLE
- asset computer-vision recognition
- full mobile native app
- multi-industry configuration
- advanced analytics dashboards
- enterprise RBAC
- enterprise SSO
- production CMMS connector
- ERP integrations
- advanced optimisation
- machine learning prediction
- long-term learning loops
- complex agent architecture
- fancy command-centre animation
- demo theatre

These are future possibilities, not current priorities.

---

# 42. SMALL DATASET IS ACCEPTABLE

The system does not need enterprise-scale data.

A strong hackathon system may use:

```text
3 assets
3 rooms
2 technicians
a few inventory records
a few incidents
a few events
a few recovery alternatives
```

That is enough if the logic is genuinely dynamic.

The requirement is **system truth**, not scale theatre.

---

# 43. WHY THIS ENGINEERING DESIGN MATTERS

The system should be explainable as:

```text
AI
→ understands ambiguity

Python
→ validates operational reality

n8n
→ coordinates systems

Postgres
→ stores organisational truth
```

This is a much stronger architecture than:

```text
LLM
→ agent
→ API calls
```

because it is safer, more reliable, easier to test, and better aligned with real enterprise deployment.

---

# 44. SUCCESS TEST

The system is technically successful when this happens truthfully:

```text
Something breaks
      ↓
Onward knows which registered asset is involved
      ↓
Onward understands the incident
      ↓
Onward understands what operation is threatened
      ↓
Onward reads actual resource state
      ↓
Onward finds one or more feasible recovery plans
      ↓
A human approves when needed
      ↓
n8n changes real systems
      ↓
the organisation continues operating
      ↓
the entire decision and execution is auditable
```

---

# 45. CORE DEVELOPMENT PRIORITY HIERARCHY

```text
#1 DATA MODEL
        ↓
#2 INCIDENT PIPELINE
        ↓
#3 AI UNDERSTANDING
        ↓
#4 IMPACT GRAPH
        ↓
#5 RECOVERY ENGINE
        ↓
#6 n8n ORCHESTRATION
        ↓
#7 REAL INTEGRATIONS
        ↓
#8 APPROVAL + SAFETY
        ↓
#9 RELIABILITY
        ↓
#10 UI
        ↓
──────────────────────────
CORE SYSTEM COMPLETE
──────────────────────────
        ↓
ONLY THEN
        ↓
DEMO + PRESENTATION
```

---

# 46. CURRENT NON-NEGOTIABLE PRODUCT TRUTH

If Onward only does:

```text
photo
→ AI diagnosis
→ work order
```

the project has failed conceptually.

The system must do:

```text
physical incident
→ operational impact
→ feasible recovery
→ coordinated execution
```

That is the product.

---

# 47. FINAL MEMORY ANCHOR FOR CLAUDE

Whenever uncertain about what to build next, return to this:

> **The job is not to repair the projector. The job is to keep the lecture running.**

Engineering translation:

> **Onward detects physical incidents, understands operational dependencies, calculates feasible recovery from real system state, pauses for human approval when needed, and uses n8n to coordinate real organisational systems.**

Do not drift away from this.


---

# MASTER VAULT USAGE NOTE

When Claude is asked to create a new repo-level `CLAUDE.md` from this vault, it should synthesize rather than blindly copy:

- keep the working `CLAUDE.md` concise enough to be operational;
- preserve all non-negotiable architecture and build-order rules;
- reflect that system build is the active phase;
- keep demo/pitch material in a clearly marked later-phase section or omit it from daily build instructions unless needed;
- never lose the product thesis, Track 2 requirements, real-integration requirement, dynamic recovery requirement, or AI/Python/n8n responsibility boundaries.
