# Star Navigator

**Star Navigator** is a Python-based interstellar navigation and procedural world-generation application built around real stellar data.

The project constructs a navigable 3D representation of the local stellar neighborhood using the **Gaia DR3 catalog**, models nearby stars as a graph based on a configurable maximum jump distance, calculates routes between real star systems, and renders those routes in an interactive 3D map.

Star Navigator also includes a **DM Generator** designed for tabletop and science-fiction worldbuilding. Game masters can define probabilistic traits that are deterministically generated for real star systems, allowing the Gaia catalog to serve as the foundation for a persistent procedurally generated universe.

---

## Features

### Real Stellar Data

Star Navigator uses Gaia stellar data to construct the local stellar environment.

The current 200-light-year catalog contains approximately:

- **104,780 Gaia stars**
- **3.65 million valid navigation edges**
- Real right ascension and declination
- Parallax-derived distances
- Gaia G-band magnitude
- BP-RP color index
- Proper motion
- Radial velocity where available

Sol is manually inserted as the origin of the navigation system.

---

## Interstellar Navigation

Stars are represented as nodes in a graph, with edges connecting systems that are within the configured maximum jump distance.

Star Navigator currently supports two routing modes:

### Shortest Distance

Finds the route that minimizes the total distance traveled between the starting system and destination.

### Fewest Jumps

Finds a route that minimizes the number of individual interstellar jumps.

A route contains real catalog systems and reports information including:

- Number of jumps
- Individual jump distances
- Total route distance
- Starting system
- Destination system

---

## Navigation Graph Caching

Constructing the complete navigation network requires evaluating a large stellar catalog and millions of possible connections.

To avoid rebuilding this graph every time Star Navigator launches, the compiled navigation graph is cached in:

```text
data/compiled/navigation_graph.pkl
```

The cached graph contains the precomputed connections between the stars in the catalog and significantly reduces application startup time.

---

## Interactive 3D Star Map

Routes can be visualized through an interactive Plotly-based 3D renderer.

The map supports:

- 3D rotation and zoom
- Configurable starfield rendering distance
- Stellar colors derived from Gaia BP-RP data
- Highlighted route systems
- Interstellar jump connections
- Start and destination markers
- Interactive hover information
- Live highlighting of systems selected from the route summary

Selecting a system in the GUI's route summary updates the system information panel and highlights the corresponding star directly on the existing Plotly visualization without rebuilding the complete map.

---

## Constellations

Star Navigator can overlay the traditional Western constellations onto the 3D stellar environment.

The constellation system includes:

- All **88 IAU constellations**
- Traditional constellation line segments
- Constellation name labels
- HIP-to-Gaia crossmatching
- Coordinate fallbacks for constellation stars unavailable in the local Gaia catalog

This allows familiar constellations such as Cygnus, Gemini, Leo, Scorpius, Boötes, and Ursa Minor to be identified within the actual 3D stellar neighborhood.

Constellation data is stored under:

```text
data/constellations/
```

and can be rebuilt using:

```text
tools/build_constellation_catalog.py
```

---

# Graphical Interface

The main application is launched through:

```text
gui_main.py
```

The GUI is built using **PySide6** and currently contains two primary interfaces.

## Navigation

The Navigation tab provides:

- Starting-system selection
- Destination selection
- Star-name autocomplete
- Route algorithm selection
- Configurable starfield radius
- Constellation line toggle
- Constellation name toggle
- Route summary
- Detailed system information
- Interactive 3D visualization

### System Information

Selecting a route system displays available Gaia information including:

- Gaia DR3 source ID
- Distance from Sol
- Right ascension
- Declination
- G magnitude
- BP-RP color index
- Proper motion
- Radial velocity
- Position within the current route
- Previous and next jump information

---

# DM Generator

Star Navigator includes a deterministic procedural-generation system intended for tabletop RPGs and science-fiction worldbuilding.

Rather than maintaining a separate fictional star catalog, the generator attaches user-defined properties directly to real Gaia systems.

The DM defines traits and their probabilities, and Star Navigator deterministically generates the results for each star.

Example traits might include:

```text
Habitable Planet
Ancient Ruins
Human Settlement
Pirate Activity
Number of Planets
Population
Number of Moons
```

---

## Boolean Traits

Boolean traits represent properties that either exist or do not exist.

Example:

```text
Trait: Ancient Ruins
Probability: 10%
Type: Boolean
```

Each system receives a deterministic existence roll.

---

## Range Traits

Range traits generate an integer when the trait occurs.

Example:

```text
Trait: Number of Planets
Probability: 50%
Type: Range
Minimum: 0
Maximum: 10
```

A generated system could therefore contain:

```text
Number of Planets: 7
```

while another system may not receive the trait at all.

---

## Deterministic Generation

Procedural generation is based on two stable identifiers:

```text
Gaia Source ID
+
Trait UUID
```

These values are hashed to generate deterministic pseudo-random rolls.

Each trait uses separate rolls for:

```text
Existence
Value
```

Conceptually:

```text
             Gaia ID + Trait UUID
                     |
          +----------+----------+
          |                     |
          v                     v
    Existence Roll          Value Roll
          |                     |
     Probability              Range
          |                     |
          v                     v
   Does trait exist?      Generated value
```

This separation means changing a trait's probability affects whether the trait appears without changing its underlying generated numeric value.

The same star and the same trait UUID will always generate the same underlying rolls.

---

## Persistent Procedural Universes

Every trait receives a UUID when it is created.

For example:

```json
{
    "id": "5ccd1f4b-566b-41b3-a376-34a675fd0172",
    "name": "Number of Planets",
    "probability": 0.5,
    "trait_type": "range",
    "minimum": 0,
    "maximum": 10
}
```

Because procedural generation uses the UUID rather than the display name, a trait can be renamed without changing the generated universe.

Deleting and recreating a trait produces a new UUID and therefore a new set of procedural results.

---

## DM Profiles

Trait configurations can be saved as JSON profiles and loaded in future sessions.

Profiles preserve:

- Trait UUID
- Trait name
- Trait type
- Probability
- Minimum range value
- Maximum range value

Because the original UUIDs are restored when a profile is loaded, generated system information remains identical across application restarts.

Generated star data itself does **not** need to be stored. It can always be reconstructed from the Gaia source ID and trait UUID.

---

## Sol

Sol is deliberately excluded from procedural generation.

```text
Sol
Manual system — procedural generation disabled.
```

This allows the DM to define the Solar System manually rather than having the procedural generator overwrite established campaign information.

---

# Project Structure

```text
Star_Navigator/
│
├── catalog.py
├── config.py
├── gui_main.py
├── main.py
├── models.py
│
├── data/
│   ├── gaia_100ly.csv
│   ├── gaia_200ly.csv
│   ├── star_names.csv
│   │
│   ├── compiled/
│   │   └── navigation_graph.pkl
│   │
│   └── constellations/
│       ├── constellation_stars.csv
│       ├── western_gaia.csv
│       └── western_index.json
│
├── dm/
│   ├── generator.py
│   ├── profiles.py
│   ├── traits.py
│   └── __init__.py
│
├── gui/
│   ├── main_window.py
│   └── __init__.py
│
├── navigation/
│   ├── graph.py
│   ├── routing.py
│   └── __init__.py
│
├── renderers/
│   ├── colors.py
│   ├── constellations.py
│   ├── interactive.py
│   ├── static.py
│   └── __init__.py
│
└── tools/
    ├── build_constellation_catalog.py
    ├── build_gaia_catalog.py
    └── Build_Star_Name_Catalog.py
```

---

# Architecture

At a high level, Star Navigator is divided into several independent systems:

```text
                 Gaia Catalog
                      |
                      v
                Star Catalog
                      |
          +-----------+-----------+
          |                       |
          v                       v
     Name Catalog          Stellar Properties
          |                       |
          +-----------+-----------+
                      |
                      v
               Navigation Graph
                      |
             +--------+--------+
             |                 |
             v                 v
       Route Finding      3D Rendering
             |                 |
             +--------+--------+
                      |
                      v
                     GUI
                      |
                      v
                DM Generator
                      |
                      v
        Deterministic World Data
```

This separation keeps astronomical data, navigation, visualization, GUI logic, and procedural world generation largely independent.

---

# Catalog Building

The `tools/` directory contains utilities used to construct Star Navigator's data files.

## Gaia Catalog Builder

```text
tools/build_gaia_catalog.py
```

Builds the local Gaia catalog used by the navigation system.

The repository currently contains:

```text
gaia_100ly.csv
gaia_200ly.csv
```

---

## Star Name Catalog Builder

```text
tools/Build_Star_Name_Catalog.py
```

Associates Gaia systems with more recognizable astronomical catalog identifiers and common names where available.

The resulting mappings are stored in:

```text
data/star_names.csv
```

---

## Constellation Catalog Builder

```text
tools/build_constellation_catalog.py
```

Processes Western constellation definitions and crossmatches their stars with Gaia systems.

The resulting constellation information is stored under:

```text
data/constellations/
```

---

# Running Star Navigator

Run the graphical application from the directory containing the `Star_Navigator` package:

```bash
python -m Star_Navigator.gui_main
```

A command-line entry point is also available through:

```bash
python -m Star_Navigator.main
```

---

# Major Python Dependencies

Star Navigator currently uses libraries including:

- **PySide6** — graphical interface
- **Plotly** — interactive 3D visualization
- **NetworkX** — navigation graph and routing
- **NumPy** — numerical operations
- **SciPy** — spatial/graph-related processing
- **Astroquery** — astronomical catalog queries used by catalog-building tools

Additional dependencies may be required by individual catalog-building utilities.

---

# Data Flow

A typical navigation session follows:

```text
Load Gaia catalog
        |
        v
Load star names
        |
        v
Load cached navigation graph
        |
        v
Select start and destination
        |
        v
Calculate route
        |
        +--------------------+
        |                    |
        v                    v
Route Summary          Interactive Map
        |
        v
System Inspector
```

The optional DM workflow extends this:

```text
Current Route
     |
     v
DM Trait Profile
     |
     v
Gaia ID + Trait UUID
     |
     v
Deterministic Generation
     |
     v
Route World Data
```

---

# Current Status

Star Navigator currently supports:

- Large Gaia-based local stellar catalogs
- Cached navigation graphs
- Interstellar route calculation
- Multiple routing strategies
- Interactive 3D route visualization
- Gaia-derived stellar colors
- Traditional constellation overlays
- Constellation labels
- GUI-based system inspection
- Live route-system highlighting
- Deterministic procedural traits
- Boolean and numeric range traits
- Multiple simultaneous DM traits
- Persistent DM profiles
- Stable procedural generation across application restarts
- Manual control of Sol

---

# Future Development

Potential future additions include:

- Direct selection of stars from the 3D map
- Additional astronomical metadata
- Improved stellar/system classification
- More procedural trait types
- Trait dependencies and hierarchical generation
- Manual overrides for individual systems
- DM campaign/world notes
- Route briefing export
- Improved profile management
- Additional map visualization controls
- Expanded stellar catalogs

---

# Purpose

Star Navigator began as an exploration of interstellar route planning using real astronomical coordinates and has grown into a combined **stellar navigation, visualization, and procedural worldbuilding platform**.

The long-term goal is to allow real astronomical data to form the physical foundation of a fictional interstellar setting while keeping navigation and procedural world generation deterministic, reproducible, and configurable by the user.