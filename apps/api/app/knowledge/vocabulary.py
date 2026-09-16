"""Shared keyword -> knowledge-graph-node vocabulary.

Used by both the retrieval term-expansion step and the conversational entity
extractor so that "the same word means the same graph concept" everywhere in
the system.
"""
from __future__ import annotations

KEYWORD_TO_NODE: dict[str, str] = {
    "soil organic carbon": "soil_organic_carbon",
    "organic carbon": "soil_organic_carbon",
    "soc": "soil_organic_carbon",
    "soil ph": "soil_ph",
    "ph": "soil_ph",
    "soil moisture": "soil_moisture",
    "moisture": "soil_moisture",
    "microbial": "soil_biological_activity",
    "soil biological activity": "soil_biological_activity",
    "soil biology": "soil_biological_activity",
    "rainfall": "rainfall",
    "precipitation": "rainfall",
    "rain": "rainfall",
    "temperature": "temperature",
    "warming": "temperature",
    "climate": "temperature",
    "water availability": "water_availability",
    "water scarcity": "water_scarcity_constraint",
    "irrigation": "water_scarcity_constraint",
    "vegetation establishment": "vegetation_establishment",
    "seedling": "vegetation_establishment",
    "monoculture": "land_use_monoculture",
    "land use change": "land_use_change",
    "land use": "land_use_monoculture",
    "fragmentation": "habitat_fragmentation",
    "habitat fragmentation": "habitat_fragmentation",
    "habitat diversity": "habitat_diversity",
    "habitat": "habitat_diversity",
    "species richness": "species_richness",
    "biodiversity": "species_richness",
    "species survival": "species_survival",
    "pollinator": "beneficial_arthropod_abundance",
    "beneficial insects": "beneficial_arthropod_abundance",
    "natural enemies": "beneficial_arthropod_abundance",
    "arthropod": "beneficial_arthropod_abundance",
    "pesticide": "pesticide_use",
    "pollution": "pesticide_use",
    "deforestation": "deforestation",
    "range shift": "species_range_shift",
    "agroforestry": "agroforestry",
    "trees": "agroforestry",
    "intercropping": "crop_diversification_intercropping",
    "crop diversification": "crop_diversification_intercropping",
    "cover crop": "cover_cropping_soil_organic_matter_management",
    "hedgerow": "native_hedgerow_habitat_strips",
    "field margin": "native_hedgerow_habitat_strips",
    "water harvesting": "water_harvesting_soil_moisture_conservation",
    "mulching": "water_harvesting_soil_moisture_conservation",
    "integrated pest management": "integrated_pest_management",
    "ipm": "integrated_pest_management",
}


def match_nodes_in_text(text: str) -> list[str]:
    lower = text.lower()
    matched: list[str] = []
    for keyword, node in KEYWORD_TO_NODE.items():
        if keyword in lower and node not in matched:
            matched.append(node)
    return matched
