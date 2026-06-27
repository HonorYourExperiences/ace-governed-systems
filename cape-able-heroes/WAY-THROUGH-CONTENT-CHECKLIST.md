# Way Through Content Checklist

**Governing Axiom:** Way Through Over Way Out (Axiom 2)  
**Purpose:** Pre-publish gate for all hero, navigation, CTA, and parent-facing copy in Cape-Able Heroes content. Every item must pass before content is published. Checklist completion is logged in the commit message and audit trail.  
**Enforced by:** `scripts/scan_content_antipatterns.py` (automated) + this manual gate (human reviewer)

---

## How to Use This Checklist

Apply to: hero copy, H1/H2 headings, navigation labels, CTA buttons, parent-facing sections, testimonial framing, and any promotional or outreach text.

For each piece of content, work through all 10 items. A single **FAIL** blocks publication until copy is revised. Mark each item ✅ PASS or ❌ FAIL with a brief note.

---

## The 10 Checklist Items

### 1. Agency Test — Who Is the Actor?
**Check:** Does every sentence that describes a transformation or improvement name the *child* (or parent) as the agent, not BYDT or the program?  
**PASS:** "Children discover their own capacity to try again."  
**FAIL:** "We help children discover their capacity to try again."  
**Why it matters:** "We help [child] do X" is rescue framing — the program is the actor, the child is the recipient. Way Through framing restores the child as the actor.

### 2. Rescue Signal Scan — Rescue Phrases Absent
**Check:** None of the following rescue-signal phrases appear in hero, H1, nav, CTA, or parent copy:
- "we help you / we help children / we help families"
- "we take care of / we handle / we do the"
- "you don't have to / you don't need to / you won't have to"
- "leave it to us / let us / we'll do it for you"
- "stress-free / worry-free / burden-free / we take the pressure off"
- "done for you / handled for you / taken care of"
- "we solve / we fix / we address your [problem]"

**PASS:** None of the above appear in high-visibility copy.  
**FAIL:** Any of the above appear in hero, heading, CTA, or parent-facing section.

### 3. Capability Modeling — Evidence of the Child's Own Power
**Check:** Does the copy include at least one observable signal that the *child* possesses capability *before* the program touches them?  
**PASS:** "Every child already holds imagination, courage, and the instinct to try." / "Cape-Able Heroes begins with the child's existing strengths."  
**FAIL:** Copy implies the child lacks capability until BYDT provides it.

### 4. Conditions Language — BYDT as Environment, Not Author
**Check:** When BYDT's role is described, is it framed as *creating conditions* rather than *producing outcomes*?  
**PASS:** "BYDT builds the conditions for children to practice courage on their own terms."  
**FAIL:** "BYDT builds courage in children." / "Our program develops resilience."

### 5. Outcome Ownership — Child Credited for Results
**Check:** When a positive outcome is named (confidence, resilience, capability, growth), is the child named as the owner of that outcome?  
**PASS:** "Children leave with evidence of their own capability — evidence they built."  
**FAIL:** "Our program gives children confidence." / "We build resilience."

### 6. Aspiration Theater Test — No Ungrounded Claims
**Check:** Every claim about outcomes is either (a) observable/measurable or (b) explicitly attributed to what the child does, not what BYDT does.  
**PASS:** "Children who complete three WonderLab sessions show measurable increase in self-initiated challenge attempts (logged in session records)."  
**FAIL:** "Transform your child." / "Watch your child become extraordinary." / "Unlock their potential."

### 7. Conditional Worth Test — No Worth-Conditional Framing
**Check:** The copy does not imply the child's worth or belonging is conditional on performance, completion, or transformation.  
**PASS:** "Every child belongs here as they are."  
**FAIL:** "Help your child become the best version of themselves." / "Give your child the tools to succeed."

### 8. Parent Framing — Witness, Not Fixer
**Check:** Parent-facing copy positions the parent as a *witness* to the child's existing capability, not as someone who needs to fix or improve the child.  
**PASS:** "You'll watch your child show you something you already suspected — they have more in them than they know."  
**FAIL:** "Help your child overcome their fears." / "Give your child the confidence they need." / "Fix the gap before it grows."

### 9. Sufficiency Signal — Present-Tense Enoughness
**Check:** At least once in any major content section, the copy communicates that the child is *already enough* in present tense — not after the program.  
**PASS:** "Cape-Able Heroes does not teach children to be brave. It reveals the bravery that was already there."  
**FAIL:** Copy only describes what the child will become, with no acknowledgment of what they already are.

### 10. Rescue-vs-Support Distinction — Clear Role Boundary
**Check:** If the content describes adult or facilitator involvement, it clearly uses support language, not rescue language.  
**PASS:** "Facilitators ask questions. They do not solve problems."  
**FAIL:** Any framing that places the adult as rescuer, problem-solver, or provider of what the child lacks.

---

## Rescue Signal → Way Through Alternative Reference

| Rescue Signal (FAIL) | Way Through Alternative (PASS) |
|---|---|
| "We help children feel capable" | "Children discover their own capability here" |
| "We build confidence" | "Children build evidence of their own confidence" |
| "We develop resilience" | "Children practice resilience — in their own way, at their own pace" |
| "Give your child the tools" | "Watch your child use what they already have" |
| "Help your child overcome" | "Watch your child move through" |
| "Transform your child" | "Witness your child as they already are — and as they grow" |
| "Unlock their potential" | "Recognize the potential that is already present" |
| "We take care of the rest" | "The rest is theirs to do — and they can" |
| "You don't have to worry" | "You'll see why there was never a reason to doubt them" |
| "Our program gives kids confidence" | "Children leave with evidence they made themselves" |

---

## Capability Signal Positive Patterns (PASS)

These phrases actively model Way Through. Their presence is a positive indicator:

- "children discover / children find / children show"
- "already capable / already brave / already imaginative"
- "creates conditions for" / "builds the space where"
- "practice on their own terms"
- "evidence they built themselves"
- "witness" (for parent/adult role)
- "move through" (not "get over" or "overcome")
- "what they already have / what was already there"
- "their own [courage/voice/capacity]"

---

## Checklist Log Entry Format

When completing this checklist before a commit, add to the commit message:

```
content-gate: WAY-THROUGH-CHECKLIST PASS — [filename] — all 10 items passed — [date]
```

If any item fails, do not commit. Revise copy, re-run `scripts/scan_content_antipatterns.py`, and re-complete the checklist.

---

*Governed by: PFMEA row — Content Creation / Rescue modeling in hero / parent copy (RPN target 48)*  
*Enforced by: prop-AGE-2026-06-27-rescue-modeling-checklist | AGE session 2026-06-27*
