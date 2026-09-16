from app.conversations.extraction import extract_from_text


def test_extracts_soc_and_ph():
    result = extract_from_text("Soil organic carbon is 0.3% and pH is 6.5.")
    assert result.fields["soil_organic_carbon"] == 0.3
    assert result.fields["soil_ph"] == 6.5


def test_extracts_rainfall_qualitative():
    result = extract_from_text("This is a very dry, drought-prone area.")
    assert result.fields["rainfall_qualitative"] == "low"


def test_extracts_biodiversity_trend_and_human_impact():
    result = extract_from_text("Pollinators are declining and we use pesticide regularly.")
    assert result.biodiversity_indicators["reported_trend"] == "declining"
    assert result.human_impact_indicators["pesticide_use"] is True


def test_does_not_hallucinate_unstated_values():
    result = extract_from_text("We are worried about our land.")
    assert result.fields == {}
    assert result.biodiversity_indicators == {}
