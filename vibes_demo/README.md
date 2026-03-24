# PandaQuest — Life Sidequests for Students

A weather-aware "sidequest" web app that gives students fun, real-life mini-challenges based on the current weather at their location. Built live in class as a **vibe coding** demo using an AI coding assistant.

## What It Does

1. Detects your location and fetches the current weather (via [Open-Meteo](https://open-meteo.com/))
2. Picks a random quest tailored to the conditions — sunny, cloudy, rainy, snowy, stormy, hot, or cold
3. Tracks a timer while you complete the quest
4. Awards XP and keeps a day-streak counter (saved in `localStorage`)

An animated panda mascot guides you through the experience.

## Tech Stack

| Layer | Details |
|-------|---------|
| **HTML** | Single-page layout (`index.html`) |
| **CSS** | Custom properties, glassmorphism, keyframe animations (`styles.css`) |
| **JS** | Vanilla ES6 — no frameworks, no build step (`app.js`) |
| **APIs** | [Open-Meteo](https://open-meteo.com/) (weather), [Nominatim/OSM](https://nominatim.openstreetmap.org/) (reverse geocoding) |

No API keys are required — both services are free and open.

## Running Locally

Because the app uses the Geolocation API, browsers require the page to be served over HTTP (not opened as a plain `file://`). Any static file server will work:

### Option A — Python (built-in)

```bash
cd vibes_demo
python3 -m http.server 3000
```

Then open <http://localhost:3000>.

### Option B — Node.js (`npx serve`)

```bash
cd vibes_demo
npx serve -l 3000
```

Then open <http://localhost:3000>.

### Option C — VS Code Live Server

Install the **Live Server** extension, right-click `index.html`, and choose *Open with Live Server*.

> **Note:** Your browser will ask for location permission — allow it so the app can look up local weather.

## Project Structure

```
vibes_demo/
├── index.html   # Page structure & inline SVG mascot
├── styles.css   # All styling, animations, and responsive layout
└── app.js       # Weather fetching, quest logic, timer, XP/streak persistence
```

## How It Was Made

This app was **vibe coded** — built conversationally with an AI assistant in a single session. The workflow looked like:

1. Describe the idea in plain language ("a quest app for students that checks the weather")
2. Let the AI generate the initial code
3. Iterate by asking for tweaks 
4. Review, test in the browser, repeat

No manual HTML/CSS/JS was written by hand — the entire app was produced through prompting.
