# Travel Planner

A multi-agent travel planner built with [Google ADK](https://google.github.io/adk-docs/).

```
travel_planner
└── travel_inspiration_agent
    ├── news_agent   -> google_search_agent (Google News)
    └── places_agent -> location_search (OpenStreetMap)
```

## Run

1. Get a Gemini API key at https://aistudio.google.com/apikey
2. `cp travel_planner/.env.example travel_planner/.env` and put your key in it
3. `uv run adk web` and open http://127.0.0.1:8000
