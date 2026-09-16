from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EnvironmentalProfileCreate(BaseModel):
    conversation_id: str | None = None
    name: str = "Untitled land profile"
    region: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    ecosystem_type: str | None = None
    land_use_type: str | None = None
    soil_ph: float | None = Field(default=None, ge=0, le=14)
    soil_organic_carbon: float | None = Field(default=None, ge=0, le=100)
    soil_moisture: float | None = Field(default=None, ge=0, le=100)
    rainfall_mm_year: float | None = Field(default=None, ge=0)
    rainfall_qualitative: str | None = None
    temperature_c: float | None = None
    biodiversity_indicators: dict[str, Any] = Field(default_factory=dict)
    human_impact_indicators: dict[str, Any] = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)
    data_source: str | None = "user_provided"
    notes: str | None = None


class EnvironmentalProfileUpdate(BaseModel):
    name: str | None = None
    region: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    ecosystem_type: str | None = None
    land_use_type: str | None = None
    soil_ph: float | None = None
    soil_organic_carbon: float | None = None
    soil_moisture: float | None = None
    rainfall_mm_year: float | None = None
    rainfall_qualitative: str | None = None
    temperature_c: float | None = None
    biodiversity_indicators: dict[str, Any] | None = None
    human_impact_indicators: dict[str, Any] | None = None
    constraints: list[str] | None = None
    notes: str | None = None


class EnvironmentalProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    conversation_id: str | None
    name: str
    region: str | None
    latitude: float | None
    longitude: float | None
    ecosystem_type: str | None
    land_use_type: str | None
    soil_ph: float | None
    soil_organic_carbon: float | None
    soil_moisture: float | None
    rainfall_mm_year: float | None
    rainfall_qualitative: str | None
    temperature_c: float | None
    biodiversity_indicators: dict[str, Any]
    human_impact_indicators: dict[str, Any]
    constraints: list[str]
    data_source: str | None
    unit_metadata: dict[str, Any]
    missing_fields: list[str]
    uncertainty_metadata: dict[str, Any]
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ObservationCreate(BaseModel):
    metric: str
    value: float
    unit: str | None = None
    observation_date: date | None = None
    source: str = "user_reported"
    confidence: str | None = None
    notes: str | None = None


class ObservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    profile_id: str
    metric: str
    value: float
    unit: str | None
    observation_date: date | None
    source: str
    confidence: str | None
    notes: str | None
