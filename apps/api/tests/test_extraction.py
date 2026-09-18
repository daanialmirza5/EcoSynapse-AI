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


def test_semiarid_ecosystem_mention_does_not_falsely_trigger_low_rainfall():
    # Regression test for a real bug found via browser red-teaming: "semi-arid"
    # contains the substring "arid", which the low-rainfall keyword list also
    # matches on -- so an explicit "rainfall is high" statement was being
    # silently overridden to "low" whenever "semi-arid" appeared in the same
    # message.
    result = extract_from_text(
        "Actually, rainfall is high, and it is a semi-arid monoculture wheat region."
    )
    assert result.fields["rainfall_qualitative"] == "high"
    assert result.fields["ecosystem_type"] == "semi-arid"


def test_semiarid_mention_alone_still_allows_explicit_low_rainfall_phrase():
    result = extract_from_text("It is a semi-arid region with low rainfall.")
    assert result.fields["rainfall_qualitative"] == "low"
