# Knowledge coverage matrix

Maps every mandatory Darukaa.Earth knowledge-area metric through the full
stack: verified sources → knowledge-graph nodes → retrieval vocabulary →
reasoning rules → recommendation types → monitoring indicators. Compiled
directly from `data/seed/*.json`, `app/knowledge/vocabulary.py`,
`app/reasoning/constraints.py`, and `app/monitoring/plans.py` — not
hand-waved from memory.

| Metric | Sources | Graph node(s) | Retrieval terms | Concern rule (threshold) | Recommendation types | Monitoring indicator |
|---|---|---|---|---|---|---|
| **Soil pH** | none (edge `e16` is an explicit `hypothesis`, no source) | `soil_ph` | "soil ph", "ph" | `extreme_soil_ph` (pH < 5.5 or > 8.5) | **None yet** — explicitly documented gap; no cataloged intervention targets pH directly (see `CONCERN_EXPLANATIONS`) | Template exists (`soil_ph`: 1:2.5 soil:water test, annual) for user-recorded observations even without a triggered recommendation |
| **Soil organic carbon** | `s1` (FAO/ITPS 2015), `s2` (Smith et al. 2021, GEB) | `soil_organic_carbon`, `soil_biological_activity` | "soil organic carbon", "organic carbon", "soc" | `low_soil_organic_carbon` (< 1.0%) | Cover cropping (`e17`, explicitly `unknown`/insufficient evidence), Agroforestry (`e10`/`e10b`, weak) | Lab test (dry combustion/Walkley-Black), annual |
| **Soil moisture** | `s9` (Journal of Soil Science & Plant Nutrition 2020) | `soil_moisture`, `vegetation_establishment` | "soil moisture", "moisture" | `low_soil_moisture` (< 20%); also reached via `water_scarcity` | Water harvesting & soil moisture conservation (`e19`, hypothesis) | Field probe / gravimetric sampling, monthly during growing season |
| **Land use / land cover** | `s3` (Tscharntke et al. 2005), `s4` (Fahrig 2003) | `land_use_monoculture`, `habitat_fragmentation` | "land use", "monoculture", "land use change" | `monoculture_land_use` (land use type contains "monoculture") | Crop diversification (`e9`, moderate), Agroforestry (`e10`, weak), Native hedgerows (`e18`, weak) | Downstream via habitat_diversity/species_richness indicators |
| **Species richness** | `s10` (Nature Communications 2018), `s11` (FAO indicators review), `s12` (intercropping meta-analysis, via `beneficial_arthropod_abundance`) | `species_richness` | "species richness", "biodiversity" | `declining_biodiversity` (user-reported trend); `deforestation_pressure` (`e13`, may_reduce) | Agroforestry, Crop diversification, Native hedgerows, IPM (all extend to species_richness via a downstream graph hop, see `reasoning/engine.py`'s one-hop extension) | Standardized species survey (transect/point-count), seasonal or annual |
| **Habitat diversity** | `s3`, `s5` (Mupepele et al. 2021), `s6` (Boinot et al. 2022) | `habitat_diversity` | "habitat diversity", "habitat" | Reached via `monoculture_land_use` and `declining_biodiversity` | Agroforestry (`e10`/`e10b`), Native hedgerows (`e18`) | Structured vegetation/habitat-structure survey, annual |
| **Temperature** | `s8` (Environmental Evidence 2023) | `temperature`, `species_range_shift` | "temperature", "warming", "climate" | `high_temperature` (> 30°C) — **added during this pass**; previously temperature was tracked as a known variable and linked in the graph (`e14`/`e15`) but had no independent concern-detection rule, meaning it could never on its own surface a candidate intervention. Now maps to water-retention interventions with an explicit "general inference, not a source-specific test" caveat. | Water harvesting & soil moisture conservation | No dedicated metric template (temperature isn't itself a monitored *outcome* metric in this catalog; it's an input condition) |
| **Rainfall** | `s9` | `rainfall`, `water_availability` | "rainfall", "precipitation", "rain" | `water_scarcity` (qualitative "low" or < 500mm/year) | Water harvesting & soil moisture conservation | N/A (input condition, not a monitored outcome) |
| **Pollution** | `s7` (Frontiers in Environmental Science 2021) | `pesticide_use` | "pesticide", "pollution" | `pesticide_pressure` (human_impact_indicators.pesticide_use) | Integrated pest management (`e12`, model_derived; `e11`, moderate) | Farm input records (applications per season) |
| **Deforestation** | `s10` (Nature Communications 2018) | `deforestation` | "deforestation" | `deforestation_pressure` (human_impact_indicators.deforestation) | Agroforestry, Native hedgerows | Downstream via habitat_diversity/species_richness |

## Coverage gaps, stated honestly

- **Soil pH has no cataloged intervention.** The concern is detected and
  explained to the user, but no candidate recommendation is generated
  purely from a pH concern today. A real fix would require sourcing a
  verified intervention (e.g. lime/sulfur amendment practices) with
  genuine evidence — not adding an untested one just to fill the cell.
- **Temperature's concern rule (`high_temperature`) was added during this
  pass** after this matrix exercise surfaced that it was missing; see
  `apps/api/tests/test_evaluation_benchmark.py::test_high_temperature_is_detected_as_a_concern`
  for the regression test.
- **Land cover** is currently folded into `land_use_type` (a single free-text
  field) rather than a separate structured land-cover taxonomy; this is
  adequate for the demo corpus's coverage but would need its own field if
  the intervention catalog grows to distinguish, e.g., cropland from
  pastureland from forest more granularly.
- **Rainfall and temperature are input conditions, not monitored outcome
  metrics** in `monitoring/plans.py` — they don't need a "measurement
  method" template because they describe the site's existing climate, not
  something an intervention is expected to change.

## How this matrix stays honest over time

Every cell above traces to a real file and line, not a description written
once and left to drift: `scripts/validate_knowledge.py` (run in CI) checks
that every relationship's `source_id` actually exists in `sources.json`, and
`apps/api/tests/test_evaluation_benchmark.py` exercises the concern-to-
recommendation mapping for every row with a non-empty "Recommendation types"
column.
