# API Specification

## Nigehbaan — Backend REST API

**Base URL:** `https://api.nigehbaan.pk/api/v1` (production) / `http://localhost:8000/api/v1` (development)
**Format:** JSON (application/json) and GeoJSON (application/geo+json)
**Authentication:** Public endpoints require no auth. Admin endpoints require Bearer token via NextAuth.js.
**Rate Limiting:** 10 requests/second for public endpoints. 50 requests/second for authenticated government users.

---

## 1. Map Endpoints

### GET /map/boundaries

Returns administrative boundary polygons as GeoJSON FeatureCollection.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `level` | integer | No | 2 | Admin level: 0=country, 1=province, 2=district, 3=tehsil |
| `province` | string | No | - | Filter by province P-code (e.g., `PK04` for Punjab) |
| `simplify` | float | No | 0.001 | Geometry simplification tolerance (degrees). Higher = simpler polygons, faster response. |

**Response (200):**

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "pcode": "PK0401",
        "name_en": "Lahore",
        "name_ur": "لاہور",
        "admin_level": 2,
        "parent_pcode": "PK04",
        "population_total": 11126285,
        "population_male": 5909379,
        "population_female": 5216906,
        "area_sqkm": 1772.0
      },
      "geometry": {
        "type": "MultiPolygon",
        "coordinates": [[[...]]]
      }
    }
  ]
}
```

---

### GET /map/incidents

Returns geocoded incident points as GeoJSON, filtered by year, type, and geography.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `year` | integer | No | - | Filter by specific year |
| `year_from` | integer | No | - | Start of year range |
| `year_to` | integer | No | - | End of year range |
| `type` | string | No | - | Incident type: `kidnapping`, `sexual_abuse`, `bonded_labor`, `trafficking`, `child_marriage`, `begging`, `missing` |
| `province` | string | No | - | Province P-code |
| `district` | string | No | - | District P-code |
| `source` | string | No | - | Source type: `sahil`, `ssdo`, `ctdc`, `news`, `court` |
| `limit` | integer | No | 1000 | Max features returned |
| `offset` | integer | No | 0 | Pagination offset |

**Response (200):**

```json
{
  "type": "FeatureCollection",
  "metadata": {
    "total_count": 4523,
    "returned": 1000,
    "offset": 0
  },
  "features": [
    {
      "type": "Feature",
      "properties": {
        "id": 12345,
        "source_type": "sahil",
        "incident_type": "kidnapping",
        "sub_type": "with_sexual_abuse",
        "year": 2024,
        "month": 3,
        "district_pcode": "PK0401",
        "district_name": "Lahore",
        "victim_count": 1,
        "victim_gender": "female",
        "victim_age_bracket": "11-15",
        "perpetrator_type": "acquaintance",
        "fir_registered": true,
        "geocode_confidence": 0.85
      },
      "geometry": {
        "type": "Point",
        "coordinates": [74.3587, 31.5204]
      }
    }
  ]
}
```

---

### GET /map/kilns

Returns brick kiln point markers as GeoJSON.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `district` | string | No | - | Filter by district P-code |
| `province` | string | No | - | Filter by province P-code |
| `kiln_type` | string | No | - | Filter by kiln type: `FCBK`, `ZigZag` |
| `min_population` | integer | No | - | Filter kilns with population_1km >= this value |
| `limit` | integer | No | 5000 | Max features returned |

**Response (200):**

```json
{
  "type": "FeatureCollection",
  "metadata": {
    "total_count": 11234,
    "returned": 5000
  },
  "features": [
    {
      "type": "Feature",
      "properties": {
        "id": 1,
        "kiln_type": "FCBK",
        "nearest_school_m": 450.2,
        "nearest_hospital_m": 3200.5,
        "population_1km": 2340,
        "district_pcode": "PK0435",
        "district_name": "Sheikhupura"
      },
      "geometry": {
        "type": "Point",
        "coordinates": [73.9862, 31.7131]
      }
    }
  ]
}
```

---

### GET /map/routes

Returns trafficking route geometries as GeoJSON LineStrings.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `trafficking_type` | string | No | - | Filter: `labor`, `sexual`, `organ`, `begging`, `marriage` |
| `confidence` | string | No | - | Minimum confidence: `high`, `medium`, `low` |

**Response (200):**

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "id": 1,
        "route_name": "Southern Punjab to Sindh Brick Kiln Corridor",
        "origin_pcode": "PK0427",
        "origin_name": "Muzaffargarh",
        "destination_pcode": "PK0303",
        "destination_name": "Hyderabad",
        "trafficking_type": "labor",
        "confidence_level": "high",
        "evidence_source": "TIP Report 2024, ILO field study",
        "year_documented": 2024,
        "transit_points": [
          {"name": "Multan", "pcode": "PK0426"},
          {"name": "Sukkur", "pcode": "PK0329"}
        ]
      },
      "geometry": {
        "type": "LineString",
        "coordinates": [[70.6, 30.2], [71.4, 29.4], [69.7, 27.7], [68.4, 25.4]]
      }
    }
  ]
}
```

---

### GET /map/heatmap

Returns pre-aggregated heatmap data (incident counts per district) for efficient rendering.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `year` | integer | No | latest | Year to aggregate |
| `year_from` | integer | No | - | Start of year range |
| `year_to` | integer | No | - | End of year range |
| `type` | string | No | - | Incident type filter |

**Response (200):**

```json
{
  "year_range": [2020, 2024],
  "districts": [
    {
      "pcode": "PK0401",
      "name_en": "Lahore",
      "incident_count": 342,
      "per_100k": 3.07,
      "centroid": [74.3587, 31.5204],
      "dominant_type": "sexual_abuse",
      "trend": "increasing"
    }
  ]
}
```

---

### GET /map/borders

Returns border crossing points.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `country` | string | No | - | Filter by border country: `afghanistan`, `iran`, `india`, `china` |
| `type` | string | No | - | Filter: `official`, `unofficial` |

**Response (200):**

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "id": 1,
        "name": "Torkham",
        "border_country": "afghanistan",
        "crossing_type": "official",
        "is_active": true,
        "vulnerability_score": 78.5,
        "notes": "Busiest Pakistan-Afghanistan crossing. 30,000+ daily crossings."
      },
      "geometry": {
        "type": "Point",
        "coordinates": [71.0931, 34.0859]
      }
    }
  ]
}
```

---

## 2. Dashboard Endpoints

### GET /dashboard/trends

Returns time series data for trend analysis charts.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `source` | string | No | `sahil` | Data source: `sahil`, `ssdo`, `ctdc`, `tip` |
| `years` | string | No | `2010-2024` | Year range (e.g., `2015-2024`) |
| `province` | string | No | - | Province P-code filter |
| `type` | string | No | - | Incident type filter |

**Response (200):**

```json
{
  "source": "sahil",
  "year_range": [2010, 2024],
  "series": [
    {
      "year": 2010,
      "total": 2388,
      "kidnapping": 780,
      "sexual_abuse": 1040,
      "trafficking": 98,
      "child_marriage": 124,
      "missing": 346
    },
    {
      "year": 2024,
      "total": 7608,
      "kidnapping": 2437,
      "sexual_abuse": 2954,
      "trafficking": 586,
      "child_marriage": 53,
      "missing": 578
    }
  ]
}
```

---

### GET /dashboard/province-comparison

Returns province-level aggregated data for comparison charts.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `year` | integer | No | latest | Year to compare |
| `type` | string | No | - | Incident type filter |

**Response (200):**

```json
{
  "year": 2024,
  "provinces": [
    {
      "pcode": "PK04",
      "name_en": "Punjab",
      "total_incidents": 6083,
      "per_100k": 5.4,
      "top_type": "sexual_abuse",
      "conviction_rate": 0.008
    },
    {
      "pcode": "PK02",
      "name_en": "Khyber Pakhtunkhwa",
      "total_incidents": 1102,
      "per_100k": 3.1,
      "top_type": "kidnapping",
      "conviction_rate": 0.005
    },
    {
      "pcode": "PK03",
      "name_en": "Sindh",
      "total_incidents": 354,
      "per_100k": 0.7,
      "top_type": "trafficking",
      "conviction_rate": 0.003
    },
    {
      "pcode": "PK06",
      "name_en": "Islamabad",
      "total_incidents": 138,
      "per_100k": 6.5,
      "top_type": "sexual_abuse",
      "conviction_rate": 0.012
    },
    {
      "pcode": "PK01",
      "name_en": "Balochistan",
      "total_incidents": 69,
      "per_100k": 0.5,
      "top_type": "kidnapping",
      "conviction_rate": 0.002
    }
  ]
}
```

---

### GET /dashboard/case-types

Returns incident type breakdown for pie/donut charts.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `province` | string | No | - | Province P-code |
| `year` | integer | No | latest | Year filter |
| `year_from` | integer | No | - | Start of year range |
| `year_to` | integer | No | - | End of year range |

**Response (200):**

```json
{
  "year": 2024,
  "total": 7608,
  "types": [
    {"type": "sexual_abuse", "count": 2954, "percentage": 38.8},
    {"type": "kidnapping", "count": 2437, "percentage": 32.0},
    {"type": "child_labour", "count": 895, "percentage": 11.8},
    {"type": "physical_abuse", "count": 683, "percentage": 9.0},
    {"type": "trafficking", "count": 586, "percentage": 7.7},
    {"type": "child_marriage", "count": 53, "percentage": 0.7}
  ]
}
```

---

### GET /dashboard/conviction-rates

Returns prosecution vs. conviction rate time series from TIP Report data.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `years` | string | No | `2015-2024` | Year range |

**Response (200):**

```json
{
  "year_range": [2015, 2024],
  "series": [
    {
      "year": 2024,
      "tier_ranking": "Tier 2",
      "ptpa_investigations": 1607,
      "ptpa_prosecutions": 812,
      "ptpa_convictions": 495,
      "conviction_rate": 0.308,
      "ppc_investigations": 23629,
      "ppc_convictions": 1245,
      "victims_identified": 19954
    }
  ]
}
```

---

### GET /dashboard/summary

Returns top-level summary statistics for animated counters on the landing page and dashboard.

**Response (200):**

```json
{
  "total_incidents_mapped": 52340,
  "districts_covered": 134,
  "data_sources_integrated": 35,
  "brick_kilns_mapped": 11234,
  "years_of_data": 15,
  "citizen_reports": 847,
  "court_judgments": 2341,
  "last_updated": "2026-03-19T00:00:00Z"
}
```

---

## 3. District Endpoints

### GET /districts

Returns all districts with basic statistics for list views and search.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `province` | string | No | - | Filter by province P-code |
| `sort` | string | No | `name_en` | Sort field: `name_en`, `population`, `risk_score`, `incident_count` |
| `order` | string | No | `asc` | Sort order: `asc`, `desc` |
| `search` | string | No | - | Search district by name (fuzzy matching) |

**Response (200):**

```json
{
  "total": 160,
  "districts": [
    {
      "pcode": "PK0401",
      "name_en": "Lahore",
      "name_ur": "لاہور",
      "province_pcode": "PK04",
      "province_name": "Punjab",
      "population_total": 11126285,
      "incident_count": 342,
      "risk_score": 67.3,
      "kiln_count": 245,
      "latest_year": 2024
    }
  ]
}
```

---

### GET /districts/{pcode}

Returns the full district profile including vulnerability indicators, incident trends, and comparisons.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pcode` | string | Yes | District P-code (e.g., `PK0401`) |

**Response (200):**

```json
{
  "pcode": "PK0401",
  "name_en": "Lahore",
  "name_ur": "لاہور",
  "province": "Punjab",
  "province_pcode": "PK04",
  "population_total": 11126285,
  "population_male": 5909379,
  "population_female": 5216906,
  "population_urban": 9245000,
  "population_rural": 1881285,
  "area_sqkm": 1772.0,
  "risk_score": 67.3,
  "risk_rank": 12,
  "risk_rank_total": 160,
  "vulnerability_indicators": {
    "poverty_headcount_ratio": 0.12,
    "school_dropout_rate": 0.08,
    "child_labor_rate": 0.04,
    "child_marriage_rate": 0.03,
    "brick_kiln_density_per_sqkm": 0.138,
    "flood_affected_pct": 0.0,
    "birth_registration_rate": 0.72,
    "distance_to_border_km": 312.5
  },
  "incident_summary": {
    "total_all_years": 1245,
    "total_current_year": 342,
    "year_over_year_change": 0.12,
    "trend": "increasing",
    "top_types": [
      {"type": "sexual_abuse", "count": 145},
      {"type": "kidnapping", "count": 98},
      {"type": "trafficking", "count": 34}
    ]
  },
  "kiln_count": 245,
  "nearest_border_crossing": {
    "name": "Wagah",
    "country": "india",
    "distance_km": 24.5
  },
  "comparison": {
    "national_avg_risk_score": 45.2,
    "province_avg_risk_score": 52.1,
    "national_avg_incidents_per_100k": 2.8,
    "district_incidents_per_100k": 3.07
  }
}
```

**Response (404):**

```json
{
  "detail": "District not found",
  "pcode": "INVALID"
}
```

---

### GET /districts/{pcode}/incidents

Returns incidents for a specific district.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pcode` | string | Yes | District P-code |

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `years` | string | No | `2020-2024` | Year range |
| `type` | string | No | - | Incident type filter |
| `limit` | integer | No | 100 | Max results |

**Response (200):** Same format as `/map/incidents` but filtered to the specific district.

---

### GET /districts/{pcode}/vulnerability

Returns detailed vulnerability indicator breakdown for a district.

**Response (200):**

```json
{
  "pcode": "PK0401",
  "name_en": "Lahore",
  "year": 2024,
  "risk_score": 67.3,
  "indicators": [
    {
      "name": "incident_rate_per_100k",
      "value": 3.07,
      "weight": 0.25,
      "weighted_score": 19.2,
      "national_avg": 2.8,
      "percentile": 72
    },
    {
      "name": "poverty_headcount_ratio",
      "value": 0.12,
      "weight": 0.15,
      "weighted_score": 8.1,
      "national_avg": 0.24,
      "percentile": 35
    },
    {
      "name": "brick_kiln_density",
      "value": 0.138,
      "weight": 0.10,
      "weighted_score": 11.5,
      "national_avg": 0.042,
      "percentile": 85
    }
  ],
  "methodology": "Composite score based on 10 weighted indicators normalized to 0-100 scale. See /about for full methodology."
}
```

---

## 4. Public Reporting Endpoints

### POST /reports

Submit a new citizen report. Authentication is not required.

**Request Body:**

```json
{
  "report_type": "suspicious_activity",
  "description": "Group of children (approx 8-10) seen being led by two adults near the brick kiln area. Children appeared distressed.",
  "location": {
    "latitude": 31.4512,
    "longitude": 74.3587,
    "address_detail": "Near GT Road, opposite the brick kiln cluster"
  },
  "incident_date": "2026-03-18",
  "photos": ["base64_encoded_image_data..."],
  "reporter_name": null,
  "reporter_contact": null,
  "is_anonymous": true
}
```

**Validation Rules:**
- `report_type` must be one of: `suspicious_activity`, `missing_child`, `bonded_labor`, `begging_ring`, `child_marriage`, `other`
- `description` must be 10-2000 characters
- `location.latitude` must be between 23.5 and 37.1 (Pakistan bounds)
- `location.longitude` must be between 60.8 and 77.8 (Pakistan bounds)
- Photos: max 3, each max 5MB, JPEG/PNG only
- Rate limit: 5 reports per IP per 24 hours

**Response (201):**

```json
{
  "id": "RPT-2026-03-00847",
  "status": "submitted",
  "created_at": "2026-03-19T14:30:00Z",
  "district_pcode": "PK0401",
  "district_name": "Lahore",
  "message": "Thank you for your report. Your reference number is RPT-2026-03-00847.",
  "helplines": {
    "emergency": "1099 (MoHR Helpline)",
    "missing_children": "0800-22444 (Roshni Helpline)",
    "child_abuse": "1098 (Madadgaar)"
  }
}
```

**Response (429 - Rate Limited):**

```json
{
  "detail": "Too many reports submitted. Maximum 5 reports per day. Please try again tomorrow or call 1099 for immediate assistance."
}
```

---

### GET /reports/{id}

Check the status of a submitted report.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string | Yes | Report reference number (e.g., `RPT-2026-03-00847`) |

**Response (200):**

```json
{
  "id": "RPT-2026-03-00847",
  "report_type": "suspicious_activity",
  "status": "verified",
  "status_history": [
    {"status": "submitted", "timestamp": "2026-03-19T14:30:00Z"},
    {"status": "verified", "timestamp": "2026-03-19T16:45:00Z"}
  ],
  "referred_to": "District Police Officer, Lahore",
  "created_at": "2026-03-19T14:30:00Z",
  "updated_at": "2026-03-19T16:45:00Z"
}
```

---

## 5. Legal Endpoints

### GET /legal/search

Search court judgments with filters.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `section` | string | No | - | PPC section: `366-A`, `366-B`, `369`, `370`, `371-A`, `371-B` |
| `court` | string | No | - | Court code: `scp`, `lhc`, `shc`, `phc`, `bhc`, `ihc` |
| `year` | integer | No | - | Judgment year |
| `year_from` | integer | No | - | Start year |
| `year_to` | integer | No | - | End year |
| `verdict` | string | No | - | Outcome: `convicted`, `acquitted`, `dismissed`, `pending` |
| `district` | string | No | - | Incident district P-code |
| `q` | string | No | - | Full-text search in judgment text |
| `limit` | integer | No | 20 | Max results |
| `offset` | integer | No | 0 | Pagination offset |

**Response (200):**

```json
{
  "total": 145,
  "returned": 20,
  "offset": 0,
  "judgments": [
    {
      "id": 1234,
      "court_name": "Lahore High Court",
      "court_bench": "Lahore",
      "case_number": "Crl. Appeal No. 1234/2023",
      "judgment_date": "2023-11-15",
      "judge_names": ["Justice Ahmad Ali"],
      "ppc_sections": ["370", "371-A"],
      "statutes": ["PTPA 2018"],
      "is_trafficking_related": true,
      "trafficking_type": "labor",
      "incident_district_pcode": "PK0435",
      "incident_district_name": "Sheikhupura",
      "verdict": "convicted",
      "sentence": "7 years RI and fine of Rs. 500,000",
      "sentence_years": 7.0,
      "source_url": "https://data.lhc.gov.pk/...",
      "nlp_confidence": 0.92
    }
  ]
}
```

---

### GET /legal/conviction-rates

Returns conviction rate statistics aggregated by district or province.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `level` | string | No | `province` | Aggregation level: `province`, `district`, `court` |
| `year_from` | integer | No | - | Start year |
| `year_to` | integer | No | - | End year |
| `section` | string | No | - | Filter by PPC section |

**Response (200):**

```json
{
  "level": "province",
  "data": [
    {
      "pcode": "PK04",
      "name_en": "Punjab",
      "total_cases": 890,
      "convicted": 234,
      "acquitted": 456,
      "pending": 200,
      "conviction_rate": 0.263,
      "avg_sentence_years": 5.2
    }
  ]
}
```

---

## 6. Search Endpoint

### GET /search

Full-text search across all data: incidents, court judgments, news articles, districts, and locations.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `q` | string | Yes | - | Search query (English or Urdu) |
| `type` | string | No | - | Filter result type: `incident`, `judgment`, `news`, `district`, `location` |
| `limit` | integer | No | 20 | Max results per type |

**Response (200):**

```json
{
  "query": "kasur trafficking",
  "total_results": 47,
  "results": {
    "districts": [
      {
        "type": "district",
        "pcode": "PK0410",
        "name_en": "Kasur",
        "relevance_score": 0.95,
        "incident_count": 89,
        "risk_score": 72.1
      }
    ],
    "incidents": [
      {
        "type": "incident",
        "id": 5678,
        "title": "Child trafficking ring busted in Kasur",
        "year": 2023,
        "source_type": "news",
        "relevance_score": 0.88
      }
    ],
    "judgments": [
      {
        "type": "judgment",
        "id": 2345,
        "case_number": "Crl. Appeal 567/2022",
        "court_name": "Lahore High Court",
        "relevance_score": 0.82
      }
    ],
    "news": [
      {
        "type": "news",
        "id": 8901,
        "title": "Police rescue 12 children from trafficking in Kasur",
        "source_name": "Dawn",
        "published_date": "2024-02-15",
        "relevance_score": 0.91
      }
    ]
  }
}
```

---

## 7. Export Endpoints

### GET /export/csv

Export filtered data as a CSV download.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `table` | string | Yes | - | Table to export: `incidents`, `kilns`, `judgments`, `vulnerability`, `tip_annual` |
| `province` | string | No | - | Province filter |
| `district` | string | No | - | District filter |
| `year_from` | integer | No | - | Start year |
| `year_to` | integer | No | - | End year |
| `type` | string | No | - | Incident type filter (for incidents table) |

**Response (200):** `Content-Type: text/csv` with `Content-Disposition: attachment; filename="nigehbaan_incidents_2024.csv"`

---

### GET /export/geojson

Export spatial data as GeoJSON download.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `layer` | string | Yes | - | Layer to export: `boundaries`, `kilns`, `incidents`, `routes`, `borders` |
| `district` | string | No | - | District filter |
| `province` | string | No | - | Province filter |
| `level` | integer | No | 2 | Admin level (for boundaries) |

**Response (200):** `Content-Type: application/geo+json` with `Content-Disposition: attachment; filename="nigehbaan_kilns_PK0401.geojson"`

---

## 8. Error Responses

All endpoints return consistent error responses:

**400 Bad Request:**
```json
{
  "detail": "Invalid parameter: 'year' must be between 2000 and 2026",
  "error_code": "INVALID_PARAMETER"
}
```

**404 Not Found:**
```json
{
  "detail": "District not found",
  "error_code": "NOT_FOUND"
}
```

**429 Too Many Requests:**
```json
{
  "detail": "Rate limit exceeded. Maximum 10 requests per second.",
  "error_code": "RATE_LIMITED",
  "retry_after": 1
}
```

**500 Internal Server Error:**
```json
{
  "detail": "An internal error occurred. Please try again later.",
  "error_code": "INTERNAL_ERROR"
}
```

---

## 9. Authentication

Public endpoints (all GET endpoints and POST /reports) require no authentication.

Admin endpoints (report moderation, scraper management, data uploads) require a Bearer token:

```
Authorization: Bearer <jwt_token>
```

Tokens are issued by NextAuth.js and validated by the FastAPI backend using the shared `NEXTAUTH_SECRET`.

---

*For implementation details, see [ARCHITECTURE.md](ARCHITECTURE.md). For database schema behind these endpoints, see [DATA_DICTIONARY.md](DATA_DICTIONARY.md).*
