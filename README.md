# Civ Sim Restart

This is a fresh restart of the project.

The current code only establishes the groundwork:
- pygame app loop
- world container
- renderer
- grid/tile drawing
- base node types for static and dynamic objects

## Run

```bash
python3 main.py
```

## Structure

- `sim/core/app.py`: bootstraps pygame and runs the main loop
- `sim/core/config.py`: screen, grid, and timing settings
- `sim/core/world.py`: owns node storage and update flow
- `sim/core/render.py`: draws the grid and nodes
- `sim/nodes/base.py`: base node types and shared data
- `sim/nodes/kinds.py`: concrete starter node types

## Current Goal

Keep the foundation small enough to understand, then add behavior one layer at a time.
# simulation
