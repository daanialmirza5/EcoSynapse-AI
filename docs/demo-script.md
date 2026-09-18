# Demo scripts (60s / 3min / 5min)

Prerequisites: backend running on `:8000`, frontend on `:5173` (see README
§11). Open the frontend at `http://localhost:5173`.

## 60-second version

Use when you only get one breath. Skip the workspace UI entirely -- narrate
over a single pre-loaded assessment screen (run the demo scenario before you
start talking so it's already on screen).

> "EcoSynapse AI is an ecological decision-support system, not a chatbot
> with green branding. Every recommendation you see here" -- point at a
> recommendation card -- "is backed by a real, verified scientific source
> with a DOI, not an LLM guess. Watch: this one" -- point at the
> Agroforestry card -- "has low confidence, because the actual 2021
> meta-analysis it cites found *no unequivocal biodiversity effect* --
> the system reports that honestly instead of a generic 'plant more trees.'
> And this monitoring plan never invents a number: it says 'establish a
> baseline first,' because no source in the corpus supports a specific
> target. The reasoning, retrieval, and verification are all deterministic
> Python, not a prompt -- the LLM, when used at all, only rephrases text for
> tone, never originates a fact."

## 3-minute version

1. **(20s) The problem.** Landholder describes declining biodiversity;
   generic chatbots either ask nothing or give generic, evidence-free advice.
2. **(30s) Structured input -> assessment.** Load the demo scenario in the
   Workspace, click Run assessment. Point out: 4 known variables, concern
   detection (low SOC, water scarcity, monoculture, declining biodiversity),
   5 candidate interventions.
3. **(45s) Evidence, not vibes.** Expand one recommendation's evidence
   table. Show the citation, the excerpt, and the evidence-status badge.
   Contrast a `supported` claim (intercropping, moderate evidence) against
   the `partially_supported` agroforestry claim -- explain the automatic
   downgrade logic (ecosystem mismatch / unverifiable numbers).
4. **(30s) Never a fabricated number.** Show the monitoring plan's "establish
   a baseline first" wording.
5. **(30s) Change and reassess.** Edit soil pH in Profile Editor, reassess,
   show the version bump and diff.
6. **(25s) Technical differentiation.** Close on Methodology: deterministic
   reasoning engine, knowledge graph, hybrid retrieval, claim verification --
   the LLM is optional and phrasing-only.

## Five-minute version

## 1. The problem (30s)
Open **Overview**. Explain: a landholder describes declining biodiversity;
generic LLM chatbots either ask nothing or immediately hand out generic
advice ("plant more trees!") with no evidence, no metrics, no honesty about
uncertainty. EcoSynapse AI is built to do the opposite.

## 2. Incomplete input (30s)
Go to **Assessment Workspace**. Type: *"Biodiversity is declining on my
land."* Show the assistant's reply: it does **not** answer — it asks up to 3
targeted clarifying questions (region/ecosystem, land use, rainfall) and
shows profile completeness at ~11%.

## 3. Clarifying questions in action (already shown above)
Point out the questions are prioritized (region and land use before soil pH)
— "a smaller number of high-value questions," not an interrogation.

## 4. Structured environmental data (30s)
Send the challenge's illustrative scenario: *"It is a semi-arid region with
monoculture wheat cropland, low rainfall, soil organic carbon 0.3%, and
pollinators seem to be declining."* Show the Environmental Profile panel
populate live: ecosystem type, land use, SOC, rainfall qualitative,
biodiversity indicator — all extracted deterministically, visible immediately.

## 5. Retrieval and knowledge graph (45s)
Switch to **Evidence Explorer**. Run the pre-filled retrieval query. Point
out the trace: graph concepts matched, terms expanded via the knowledge
graph, semantic vs. lexical candidate counts, and per-result "why matched"
reasons. Then open **Knowledge Graph**, filter to `intervention` nodes, click
`agroforestry`, and show its typed edges with evidence-strength color coding.

## 6. Multi-variable reasoning (30s)
Back in the **Workspace**, click **Run assessment**. Show the assessment
summary: *"Considered 4 known variable(s)... Soil organic carbon is below
1%... Rainfall is reported as low... monoculture... declining biodiversity
trend."* Expand the reasoning trace to show the graph paths behind each
candidate.

## 7. Compare candidate interventions (45s)
Open **Recommendation Comparison**. Show the ranked table: time horizon,
confidence, impacted metrics, supported-claim ratio, heuristic score — and
say out loud that the heuristic is explicitly labeled a prototype, not a
validated biodiversity index.

## 8. Claim-level evidence (45s)
Back in the Workspace, expand the **Agroforestry** recommendation's evidence
table. Read the honest finding aloud: *"no unequivocal effect on
biodiversity"* — this is the actual conclusion of the cited 2021
meta-analysis, and the system reports it instead of a rosier summary. Contrast
with the **Crop diversification** recommendation, which has genuinely
`moderate`-strength, `supported` evidence (36%/94%/27% increases from a real
meta-analysis).

## 9. Monitoring plan (30s)
Still expanded, show the monitoring plan table: method, frequency, and the
target column reading *"Establish a baseline first..."* — emphasize that no
number was invented.

## 10. Change an input (20s)
Go to **Profile Editor**, change soil pH to `7.2`, save.

## 11. Reassess and show adaptation (30s)
Back in Workspace, click **Reassess**. Show the version bump (v1 → v2) and
the diff panel calling out exactly the `soil_ph` field change.

## 12. Technical differentiation (30s)
Close on **Methodology**: the reasoning engine is deterministic Python, not
an LLM prompt; the LLM (when configured at all) only rephrases already-correct
text for tone and never originates a claim, number, or citation; every
citation in this demo was verified via live search during development, not
recalled from memory.

---

**Total: ~5 minutes.** If time-constrained, prioritize steps 4, 6, 8, 9, 11 —
they are the ones that most directly demonstrate depth of reasoning (30%),
scientific grounding (25%), and knowledge system design (20%).
