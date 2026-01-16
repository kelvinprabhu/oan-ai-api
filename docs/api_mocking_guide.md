# API Mocking Guide for Agent Tools

This document outlines the Request and Response structures for the tools in `agents/tools`. It is primarily focused on tools that communicate with an external BAP (Beckn Application Platform) endpoint to help you create mock API endpoints.

## 1. Mandi Prices Tool (`mandi.py`)

Retrieves market prices for agricultural commodities based on location.

### Request Structure
**Discriminators**:
- `context.domain`: `"advisory:mh-vistaar"`
- `message.intent.category.descriptor.code`: `"price-discovery"`

**Sample Request Payload**:
```json
{
  "context": {
    "domain": "advisory:mh-vistaar",
    "action": "search",
    "location": {
      "country": {
        "name": "India",
        "code": "IND"
      }
    },
    "version": "1.1.0",
    "bap_id": "your_bap_id",
    "bap_uri": "your_bap_uri",
    "message_id": "uuid-string",
    "transaction_id": "uuid-string",
    "timestamp": "2023-10-27T10:00:00.000Z"
  },
  "message": {
    "intent": {
      "category": {
        "descriptor": {
          "code": "price-discovery"
        }
      },
      "item": {
        "descriptor": {
          "code": ""
        }
      },
      "fulfillment": {
        "stops": [
          {
            "location": {
              "gps": "18.5204, 73.8567"
            },
            "time": {
              "range": {
                "start": "2023-10-27T00:00:00Z"
              }
            }
          }
        ]
      }
    }
  }
}
```

### Response Structure
**Sample Response Payload**:
```json
{
  "context": {
    "domain": "advisory:mh-vistaar",
    "action": "on_search",
    "version": "1.1.0",
    "bap_id": "your_bap_id",
    "bap_uri": "your_bap_uri",
    "message_id": "uuid-string",
    "transaction_id": "uuid-string",
    "timestamp": "2023-10-27T10:00:05.000Z"
  },
  "responses": [
    {
      "context": { 
        "action": "on_search", 
        "domain": "advisory:mh-vistaar", 
        "timestamp": "...", 
        "message_id": "...", 
        "transaction_id": "...", 
        "version": "1.1.0" 
      },
      "message": {
        "catalog": {
          "providers": [
            {
              "id": "provider-1",
              "descriptor": {
                "name": "APMC Pune"
              },
              "locations": [
                {
                  "id": "loc-1",
                  "city": { "name": "Pune" }
                }
              ],
              "items": [
                {
                  "id": "item-1",
                  "descriptor": {
                    "name": "Onion"
                  },
                  "location_ids": ["loc-1"],
                  "price": {
                    "minimum_value": "2000",
                    "maximum_value": "3000",
                    "estimated_value": "2500"
                  }
                }
              ]
            }
          ]
        }
      }
    }
  ]
}
```

---

## 2. Schemes Tool (`scheme.py`)

Retrieves government agricultural schemes.

### Request Structure
**Discriminators**:
- `context.domain`: `"schemes:oan"`
- `message.intent.category.descriptor.code`: `"schemes-agri"`

**Sample Request Payload**:
```json
{
  "context": {
    "domain": "schemes:oan",
    "action": "search",
    "version": "1.1.0",
    "bap_id": "your_bap_id",
    "bap_uri": "your_bap_uri",
    "message_id": "uuid-string",
    "transaction_id": "uuid-string",
    "timestamp": "..."
  },
  "message": {
    "intent": {
      "category": {
        "descriptor": {
          "code": "schemes-agri"
        }
      },
      "item": {
        "descriptor": {
          "name": "pmkisan" 
        }
      }
    }
  }
}
```
*Note: `message.intent.item.descriptor.name` can be empty string, "kcc", "pmkisan", or "pmfby".*

### Response Structure
**Sample Response Payload**:
```json
{
  "context": { "action": "on_search", "domain": "schemes:oan", "timestamp": "...", "message_id": "...", "transaction_id": "...", "version": "1.1.0" },
  "responses": [
    {
      "context": { ... },
      "message": {
        "catalog": {
          "descriptor": { "name": "Schemes Catalog" },
          "providers": [
            {
              "descriptor": { "name": "Govt of India" },
              "items": [
                {
                  "id": "pmkisan",
                  "descriptor": {
                    "name": "PM Kisan Samman Nidhi",
                    "short_desc": "Financial support for farmers"
                  },
                  "tags": [
                    {
                      "display": true,
                      "descriptor": { "name": "Benefits" },
                      "list": [
                        {
                          "descriptor": { "name": "Amount" },
                          "value": "Rs. 6000 per year"
                        }
                      ]
                    },
                    {
                        "display": true,
                        "descriptor": { "name": "Eligibility" },
                        "list": [
                            {
                                "descriptor": { "name": "Criteria" },
                                "value": "Small and marginal farmers"
                            }
                        ]
                    }
                  ]
                }
              ]
            }
          ]
        }
      }
    }
  ]
}
```

---

## 3. Warehouse Tool (`warehouse.py`)

Retrieves warehouse storage information near a location.

### Request Structure
**Discriminators**:
- `context.domain`: `"advisory:mh-vistaar"`
- `message.intent.category.descriptor.code`: `"warehouse"`

**Sample Request Payload**:
```json
{
  "context": {
    "domain": "advisory:mh-vistaar",
    "location": { "country": { "name": "IND" } },
    "action": "search",
    "version": "1.1.0",
    "bap_id": "...",
    "bap_uri": "...",
    "message_id": "...",
    "transaction_id": "...",
    "timestamp": "..."
  },
  "message": {
    "intent": {
      "category": {
        "descriptor": {
          "code": "warehouse"
        }
      },
      "item": {
        "descriptor": {
          "name": "none"
        }
      },
      "fulfillment": {
        "stops": [
          {
            "location": {
              "gps": "18.52, 73.85"
            },
            "time": {
              "range": {
                "start": "2023-10-27T00:00:00Z"
              }
            }
          }
        ]
      }
    }
  }
}
```

### Response Structure
**Sample Response Payload**:
```json
{
  "context": { ... },
  "responses": [
    {
      "context": { ... },
      "message": {
        "catalog": {
          "descriptor": { "name": "Warehouse Catalog" },
          "providers": [
            {
              "id": "provider-wh-1",
              "descriptor": { "name": "Central Warehousing Corp", "short_desc": "State owned" },
              "items": [
                {
                  "id": "wh-item-1",
                  "descriptor": { "name": "Pune Warehouse 1", "short_desc": "Cold storage available" },
                  "address": {
                    "address": "Plot 123, Ind. Area",
                    "district": "Pune",
                    "region": "Maharashtra",
                    "taluka": "Haveli",
                    "vilage": "Hadapsar",
                    "pinCode": "411028"
                  },
                  "contact": {
                    "person": "Manager",
                    "email": "contact@example.com",
                    "phone": "9876543210",
                    "webUrl": "http://example.com"
                  },
                  "price": {
                    "currency": "INR",
                    "value": "50",
                    "unit": "per sqft/month"
                  },
                  "rating": "4.5",
                  "creator": { "name": "CWC" },
                  "tags": [
                    {
                      "list": [
                        { "descriptor": { "code": "capacity" }, "value": "1000 MT" }
                      ]
                    }
                  ]
                }
              ]
            }
          ]
        }
      }
    }
  ]
}
```

---

## 4. Weather Tool (`weather.py`)

Retrieves weather forecasts for a location.

### Request Structure
**Discriminators**:
- `context.domain`: `"advisory:weather:mh-vistaar"`

**Sample Request Payload**:
```json
{
  "context": {
    "domain": "advisory:weather:mh-vistaar",
    "action": "search",
    "version": "1.1.0",
    "bap_id": "...",
    "bap_uri": "...",
    "location": { "country": { "name": "India", "code": "IND" } },
    "message_id": "...",
    "transaction_id": "...",
    "timestamp": "..."
  },
  "message": {
    "intent": {
      "category": {
        "descriptor": { "name": "Weather-Forecast" }
      },
      "item": {
        "time": {
          "range": {
            "start": "2023-10-27T00:00:00Z",
            "end": "2023-11-01T00:00:00Z"
          }
        }
      },
      "fulfillment": {
        "stops": [
          { "location": { "gps": "18.52, 73.85" } }
        ]
      }
    }
  }
}
```

### Response Structure
**Sample Response Payload**:
```json
{
  "context": { ... },
  "responses": [
    {
      "context": { ... },
      "message": {
        "catalog": {
          "descriptor": { "name": "Weather Catalog" },
          "providers": [
            {
              "id": "weather-provider",
              "descriptor": { "name": "IMD" },
              "items": [
                {
                  "id": "forecast-day-1",
                  "descriptor": {
                    "name": "2023-10-27",
                    "short_desc": "Sunny",
                    "long_desc": "Clear skies with moderate temperature"
                  },
                  "matched": true,
                  "recommended": true,
                  "tags": [
                    {
                      "descriptor": { "name": "Temperature" },
                      "list": [
                        { "descriptor": { "code": "min" }, "value": "20 C" },
                        { "descriptor": { "code": "max" }, "value": "32 C" }
                      ]
                    },
                    {
                        "descriptor": { "name": "Conditions" },
                        "list": [
                            { "descriptor": { "code": "precipitation" }, "value": "0 mm" }
                        ]
                    }
                  ]
                }
              ]
            }
          ]
        }
      }
    }
  ]
}
```

---

## 5. Other Tools

These tools do not use the BAP protocol / generic endpoint but are part of the agents toolkit.

### Search Tool (`search.py`)
- **Type**: Vector Search Client
- **Interaction**: Connects to Marqo Vector DB via `MARQO_ENDPOINT_URL`.
- **Function**: `search_documents(query, top_k, type)`
- **Response**: List of document hits with similarity scores.

### Maps Tool (`maps.py`)
- **Type**: Geocoding Client
- **Interaction**: Connects to Nominatim (OpenStreetMap) typically on `localhost:8080` (or public) via `geopy`.
- **Function**: `forward_geocode`, `reverse_geocode`
- **Response**: `Location` object.

### Terms Tool (`terms.py`)
- **Type**: Local Utility
- **Interaction**: Reads local file `assets/term_glossary.json`.
- **Function**: `search_terms`
- **Response**: Matched terms with scores.
