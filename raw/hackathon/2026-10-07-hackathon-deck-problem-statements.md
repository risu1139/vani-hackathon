# Voice AI Hackathon 2.0 deck - extracted text

Source file: Voice_AI_Hackathon_2.0_Deck_Revised - Final.pptx (project root). Extracted 2026-10-07, slide text only.

## Slide 1
9th & 10th October 2026

## Slide 2
Agenda
1
Problem Statements (7)
2
Sarvam AI Platform & Submission
3
Evaluation Process & Criteria
4
Prizes & Awards
5
2-Day Hackathon Flow & Dress Code
6
Facilities & Hackathon Rules

## Slide 3
Seven Problems to Solve for VANI and IM
Each problem has three slides: the problem statement, what you will build, and what you will deliver and how it is scored.
1
Quality Audit & Fix Loop
2
Global Context: Memory Across Channels
3
Best Time to Call
4
Persona Design
5
Agent A/B Testing & Auto-Rollout
6
Seller Enrichment

## Slide 4
Quality Audit & Fix Loop
Problem 1 of 6    |  Problem statement
The problem today
Today VANI call quality is checked by sampling a few calls into a spreadsheet. Most failures go unseen, root causes are guessed, and fixes reach the prompt slowly and by hand.
The challenge
Make VANI's calls audit themselves and get fixed automatically, instead of a sample-based spreadsheet review.

## Slide 5
What You'll Build
Problem 1  of 6    |  Quality Audit & Fix Loop
Calls that audit themselves and get fixed automatically
1
Auto-grade every call as Fatal or Non-Fatal
2
Group failures into root causes
3
Rank root causes by frequency and severity so the most impactful surface first
4
Suggest the prompt fix for each top issue
5
One dashboard showing audit, issue, fix, test
6
Flag risky calls for review: wrong requirement, frustration, loops, low confidence, human request

## Slide 6
Outputs and Scoring
Problem 1 of 6    |  Quality Audit & Fix Loop
What you hand in, and how we judge it
Expected outputs
Working audit-to-fix pipeline on real call data
Dashboard with the full audit, issue, fix, test trail
Risk-flag queue for human review
Success metrics
Agreement of auto-grades with human auditors
Share of calls audited (vs. sample today)
Quality of root-cause grouping and ranking
Drop in failure rate after a suggested fix is tested
Time from issue found to fix tested

## Slide 7
Global Context: Memory Across Channels
Problem 2  of 6    |  Problem statement
The problem today
Each call or chat starts cold. The bot does not know what the buyer searched, what the seller received, or what was said on WhatsApp yesterday, so users repeat themselves and conversations restart.
The challenge
Make VANI already know the buyer or seller, and their past history, before it speaks.

## Slide 8
What You'll Build
Problem 2  of 6    |  Global Context: Memory Across Channels
VANI already knows the user before it speaks
1
Context layer keyed to GLID, pulling history from data sources participants choose (starter API list provided, others allowed)
2
buyer.md: enquiries filed, categories searched, sellers contacted, KYC status, past conversations, engagement signals
3
seller.md: leads received, responses and call outcomes, categories and products, past conversations, engagement signals
4
Bot loads the file before each call or chat, opens with a personalised line, and resumes across voice, WhatsApp, chat and app
5
Files stay short, structured and always up to date, regenerated as new activity arrives
6
Participants pick the right lookback window

## Slide 9
Outputs and Scoring
Problem 2  of 6    |  Global Context: Memory Across Channels
What you hand in, and how we judge it
Expected outputs
Generated buyer.md and seller.md for sample GLIDs
Demo: a conversation that resumes across two channels
Note on sources used, lookback window and refresh logic
Success metrics
Freshness: delay between new activity and updated file
Compactness and structure of the files
Conversations resumed without re-asking
Lift from the personalised opening
Reusability beyond the bot prompt

## Slide 10
Best Time to Call
Problem 3  of 6    |  Problem statement
The problem today
Sellers are called on a fixed schedule with a fixed 15-minute retry rule. Nobody knows if that rule is right, and optimising only for connect rate may not produce more meetings.
The challenge
Find the right hour to call each seller, and how to retry when they don't pick up.

## Slide 11
What You'll Build
Problem 3  of 6    |  Best Time to Call
The right hour for each seller, and how to retry
1
A model on historical call data that predicts each seller's best call window
2
Retry timing for when a call is not picked up
3
Evidence on the 15-minute rule: keep, change, or supplement it
4
Optimised for meetings fixed, not just connect rate

## Slide 12
Outputs and Scoring
Problem 3  of 6    |  Best Time to Call
What you hand in, and how we judge it
Expected outputs
Trained model with per-seller window and retry predictions
Backtest against historical outcomes and the current rule
Recommendation on the 15-minute rule with supporting evidence
Success metrics
Lift in meetings fixed vs. the current schedule on held-out data
Connect rate and calls needed per meeting
Soundness of the validation method
Clarity and defensibility of the rule recommendation

## Slide 13
Persona Design
Problem 4  of 6    |  Problem statement
The problem today
VANI talks to every seller in one voice and one style, and keeps it for the whole call. Sellers differ in pace, patience, language and how they object, and a seller who gets irritated, confused or rushed mid-call still gets the same delivery.
The challenge
Before each call, build the VANI persona that fits that seller from their seller data, and adapt it live as the call unfolds.

## Slide 14
What You'll Build
Problem 4  of 6    |  Persona Design
A persona built for each seller, that adapts during the call
1
Seller data as input: profile, business type, turnover, categories, engagement, past call outcomes and objections (provided)
2
Persona generator: sets voice (gender, accent, pitch, pace), language (Hinglish mix, formality) and tone (warmth, empathy)
3
Conversation plan: opening, personalisation, objection playbook, escalation rules and guardrails, each tied to seller data
4
Evidence from past calls: which persona choices work for which seller types, from transcripts, summaries and outcomes
5
Live adaptation: spot frustration, confusion, interest, a language switch or a rush, and change the persona mid-call
6
Voice demo on Sarvam: the same scenario for 2 to 3 contrasting sellers, with at least one live mid-call switch

## Slide 15
Outputs and Scoring
Problem 4  of 6    |  Persona Design
What you hand in, and how we judge it
Expected outputs
Persona generator running on sample seller files
Persona spec per seller, with the reason for each choice
Live demo with at least one mid-call switch
Switch log: signal detected, change made, reason
Success metrics
Fit of each persona to its seller
Correct, well-timed mid-call switches
Distinctness of personas across seller types
Natural voice in 2+ languages
Support from past-call evidence

## Slide 16
Agent A/B Testing & Auto-Rollout
Problem 5  of 6    |  Problem statement
The problem today
Changes to VANI's prompt go live to all traffic on judgement alone. There is no safe way to try a change on a few calls, check whether it produces more of the outcome we want, and ship it only if it does.
The challenge
Test any change to an agent on a small, time-bound slice of calls against a chosen goal disposition, and automatically roll out only the winner.

## Slide 17
What You'll Build
Problem 5  of 6    |  Agent A/B Testing & Auto-Rollout
Test a change on a small slice, roll out only the winner
1
Write variants A and B: a full new prompt, or a few instructions changed in the current one
2
Set up the test: audience share (e.g. 10%), random assignment, a fixed time window and a goal disposition
3
Goal disposition: chosen per test, such as Meeting Fixed, Buyer Enriched or Callback Fixed
4
Auto-disposition: an LLM evaluator tags every test call, so matching dispositions are counted with no manual tagging
5
Declare the winner: the variant with the highest share of goal dispositions, checked for significance, is promoted to all traffic
6
Guardrails and test bed: stop a clearly worse variant early; test on simulated sellers built with Sarvam voice agents

## Slide 18
Outputs and Scoring
Problem 5  of 6    |  Agent A/B Testing & Auto-Rollout
What you hand in, and how we judge it
Expected outputs
Working A/B workflow end to end
Run report: split, goal-disposition share per variant, significance and decision
Demo of auto-promotion and of early stop on a worse variant
Success metrics
Right winner on a known-difference test
Accuracy of the traffic split
Accuracy of auto-disposition vs. labelled calls
Correct auto-promotion and early stop
Easy setup for any agent and goal

## Slide 19
Seller Enrichment
Problem 7  of 6    |  Problem statement
The problem today
Seller onboarding is pure form-filling automation. It is efficient for us but gives the seller no guidance, so profiles are thin and the seller feels nothing. Their real business data already exists outside IM: website, Google listing, social pages, catalogs, GST records.
The challenge
Gather a seller's locations, people names and categories from non-IM data and convert them to IM data, so onboarding feels like enrichment, not data entry.

## Slide 20
What You'll Build
Problem 7  of 6    |  Seller Enrichment
Turn a seller's non-IM data into an enriched IM profile
1
Input: minimal, such as business name, phone, website or Google link, or an uploaded card or brochure
2
Discover and extract locations, people names and categories
3
Convert to IM schema: normalised addresses, deduplicated people with roles, categories mapped to the IM taxonomy
4
Present a pre-filled, editable profile with a confidence score per field
5
Learn from seller corrections
6
Handle messy Hindi, English and Hinglish data, and respect consent and privacy

## Slide 21
Outputs and Scoring
Problem 7  of 6    |  Seller Enrichment
What you hand in, and how we judge it
Expected outputs
Demo: minimal input to pre-filled seller profile
Structured JSON aligned to IM fields, with confidence scores
Short write-up on data sources and accuracy approach
Success metrics
Fields confirmed by the seller without edits
Share of profile fields auto-populated
Drop in onboarding time and manual inputs
Category-mapping precision
Responsible use of third-party data

## Slide 22
Build on the Sarvam AI Platform
India's full-stack voice AI platform, provided to every team
1
Speech-to-Text
Saaras: speech recognition across 22 Indian languages + English, including code-mixed Hinglish
2
Text-to-Speech
Bulbul: natural Indian voices in 11 languages with control over speaker, pitch and pace
3
LLM & Translation
Sarvam LLMs for Indian-language reasoning, plus Mayura translation
4
Voice Agents
Build, test and deploy agents across telephony, WhatsApp, web widget and API
Access: Each team gets API keys / credits on dashboard.sarvam.ai. Use the Python or JavaScript SDK, REST or WebSocket APIs.
Docs: docs.sarvam.ai  |  Sarvam team members will be on the floor for platform support on both days.

## Slide 23
Submission Process
Submission window: 2:00 PM to 11:59 PM on Day 2
1
Build
Build your voice agent / solution on the Sarvam AI platform using the provided keys
2
Record
Record a 5 to 7 minute demo video showing the solution working end to end
3
Package
Prepare the solution folder: code, README, skills.md and sample outputs
4
Submit
Upload via the submission link shared on Day 1; one submission per team
Checklist
Demo video (5 to 7 min)
Problem statement chosen + approach note
Agent ID / live link on Sarvam platform
Solution folder with code and README
skills.md: your build journey and tools used
Team name and member details

## Slide 24
Evaluation Process
How your solution moves from submission to the podium
1
Submission
Day 2, 11:59 PM
All entries locked on the submission platform
2
Screening
After submissions close
Jury reviews demo video, solution folder and skills.md
3
Live demo
Date to be announced
Each team presents to the jury, followed by Q&A
4
Results
Date to be announced
Scores consolidated; winners announced at the awards
Scoring: each jury member scores every team 1 to 5 on the five criteria (next slide). Weighted scores are averaged across the jury. The jury's decision is final.

## Slide 25
Evaluation Criteria
Five criteria, scored 1 to 5 by every jury member
25%
Business Impact
Lift on the problem's success metrics; scale of benefit for VANI, buyers and sellers
20%
Solution Completeness
Share of the expected outputs delivered and working end to end
20%
Technical Robustness
Sound logic and validation on real data; handles edge cases and failures
20%
Voice Experience
Natural, low-latency conversation; multilingual and Hinglish handling
15%
Demo & skills.md
Clarity of the demo and of the documented build journey

## Slide 26
Voice AI Hackathon 2.0 Awards
Top three teams
1st Prize
Coway Airmega Air Purifier
+ Sarvam LLM Subscription
2nd Prize
Instax Mini LiPlay Camera
+ Sarvam LLM Subscription
3rd Prize
Smart Mini Projector
+ Sarvam LLM Subscription

## Slide 27
Voice AI Hackathon 2.0 Awards
Category awards and special recognitions
Category Award
Zebronics Bluetooth Soundbar
Special Recognition
🏅
Sarvam Merch
Participation
Certificate for every participant
Navratri Best Dressed
🎁🪔
Special hampers on Day 2

## Slide 28
The 2-Day Flow
9th & 10th October 2026  |  9:00 AM onwards  |  In office
Day 1   Fri, 9th Oct  |  Build
9:00 AM
Reporting & registration
9:30 AM
Breakfast
10:00 AM
Kick-off & welcome address
10:30 AM
Problem statements & Sarvam walkthrough
12:00 PM
Employee engagement activity
1:00 PM
Lunch
3:30 PM
Mentor check-in (Round 1)
5:00 PM
Refreshments
6:00 PM
Day 1 wrap-up: progress stand-up
Day 2   Sat, 10th Oct  |  Build & Submit
9:00 AM
Reporting
9:30 AM
Breakfast
10:00 AM
Hackathon resumes
12:00 PM
Navratri engagement activity
1:00 PM
Lunch
2:00 PM
Submission window opens on the platform
11:59 PM
Submission deadline

## Slide 29
Dress Code
Two days, two looks
👕
Day 1  |  Hackathon Theme
Wear your Hackathon T-shirt with trousers.
🪔
Day 2  |  Navratri Special
Come dressed in traditional Indian attire to celebrate the Navratri spirit.
🎁
Best-dressed special: participants who are best dressed in Navratri-special Indian attire on Day 2 will receive special hampers!

## Slide 30
Facilities & Hackathon Rules
What we provide
📍
Venue: 11th Floor, blocked for the hackathon
🔑
Platform: Sarvam AI API keys / credits and LLM key per team
📶
Setup: High-speed Wi-Fi and power points at every desk
🍽️
Food: Breakfast, lunch and evening refreshments on both days
🧑‍🏫
Support: Mentors and Sarvam experts on the floor
👕
Swag: Hackathon T-shirt for every participant
Rules & guidelines
Teams of 3, with at least 1 non-tech member
Each team picks one of the 7 problem statements
Bring your own laptop; all build work happens during the 2 days
Use the data provided responsibly; no customer data leaves the premises
Submit by 11:59 PM on Day 2; late entries are not evaluated
Stay on the 11th Floor and report on time both days
Plagiarised or pre-built solutions are disqualified
The jury's decision is final

## Slide 31
Thank You
