# Currency Exchanger API

A FastAPI-based REST API for managing country currency exchange rates, GDP estimates, and related information. The API fetches data from external sources, stores it in a database, and provides endpoints for CRUD operations with filtering and sorting capabilities.

## Features

- Create and manage country currency exchange data
- Bulk refresh all countries from external APIs
- Filter countries by region and currency
- Sort by GDP, population, or name
- Generate visual summary images with top GDP countries
- Real-time exchange rate integration
- Automatic GDP estimation based on population and exchange rates

## Prerequisites

- Python 3.8+
- PostgreSQL (or compatible SQL database)
- pip package manager

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd currency-exchanger-api
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

Required packages:
- fastapi
- sqlalchemy
- requests
- python-dotenv
- uvicorn
- Pillow

4. Set up environment variables:

Create a `.env` file in the root directory:
```env
COUNTRIES_RESPONSE=
EXCHANGE_RESPONSE=
DATABASE_URL=postgresql://user:password@localhost/dbname
```

5. Run database migrations:
```bash
# Create tables
alembic upgrade head
```

## Running the Application

Start the development server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

API documentation available at:
- Swagger UI: `http://localhost:8000/docs`

## API Endpoints

### Create Country
```http
POST /countries/refresh/
```
Creates a new country entry by fetching data from external APIs.

**Request Body:**
```json
{
  "name": "Nigeria",
  "population": 200000000,
  "currency_code": "NGN"
}
```

### Bulk Refresh Countries
```http
POST /countries/refresh/bulk/
```
Fetches and updates all countries from external APIs. Creates new entries and updates existing ones.

**Response:**
```json
{
  "created": 50,
  "updated": 150,
  "skipped": 10,
  "created_countries": ["Country1", "Country2", ...],
  "updated_countries": ["Country3", "Country4", ...],
  "skipped_countries": ["Country5 (no currency)", ...],
  "message": "Successfully created 50 and updated 150 countries..."
}
```

### Get All Countries
```http
GET /countries/
```

**Query Parameters:**
- `region` (optional): Filter by region (case-insensitive)
- `currency` (optional): Filter by currency code
- `sort` (optional): Sort results
  - `gdp_asc` / `gdp_desc`
  - `population_asc` / `population_desc`
  - `name_asc` / `name_desc`

**Example:**
```http
GET /countries/?region=Africa&sort=gdp_desc
```

### Get Country by Name
```http
GET /countries/{country_name}/
```

**Example:**
```http
GET /countries/Nigeria/
```

### Delete Country
```http
DELETE /countries/{country_name}/
```

### Get Country Status
```http
GET /countries/status/
```

Returns total count of countries and last refresh timestamp.

**Response:**
```json
{
  "total_countries": 200,
  "last_refreshed_at": "2025-10-27T12:00:00Z"
}
```

### Get Summary Image
```http
GET /countries/image/
```

Returns a PNG image showing:
- Total countries count
- Top 5 countries by GDP
- Last refresh timestamp

## Database Schema

### CurrencyExchanger Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| name | String | Country name |
| capital | String | Capital city |
| region | String | Geographic region |
| population | Integer | Population count |
| currency_code | String | ISO currency code |
| exchange_rate | Float | Exchange rate to base currency |
| estimated_gdp | Float | Estimated GDP |
| flag_url | String | URL to country flag image |
| last_refreshed_at | Timestamp | Last update timestamp |

## Error Handling

The API returns appropriate HTTP status codes:

- `200 OK`: Successful GET request
- `201 Created`: Successful POST request
- `204 No Content`: Successful DELETE request
- `400 Bad Request`: Invalid input data
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Image Generation

The bulk refresh endpoint automatically generates a summary image (`cache/summary.png`) containing:
- Total countries in database
- Top 5 countries by GDP
- Last refresh timestamp

The image is created using PIL/Pillow and saved locally for retrieval via the `/countries/image/` endpoint.

## Development

### Project Structure
```
.
├── src/
│   ├── database/
│   │   └── core.py
│   ├── entities/
│   │   └── currency_exchanger.py
│   └── routes/
│       ├── models.py
│       ├── services.py
│       └── router.py
├── cache/
│   └── summary.png
├── .env
├── requirements.txt
└── README.md
```

### Adding New Features

1. Define models in `models.py`
2. Implement business logic in `services.py`
3. Create API routes in `router.py`
4. Update database schema if needed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please create an issue in the repository or contact the development team.

## Acknowledgments

- External APIs for country and exchange rate data
- FastAPI framework
- SQLAlchemy ORM
- Pillow for image generation