# CAF Bot

A simple Python bot that keeps me up to date with my alpine club activities.

## Usage

Create a and activate a virtual environment with:

```bash
python -m virtualenv ven

# Windows
venv\Scripts\activate

# Linux
source venv/Scripts/activate
```

Create a `clubot.yaml` containing the following:

```yaml
# Email secrete (DO NOT COMMIT!)
SECRET: null

# Base path to section agendas.
agenda: https://www.clubalpinlyon.fr/agenda

# List of sub-sections to query.
activities:
  - alpinisme
  - canyon
  - escalade
  - raquette
  - ski-de-randonnee
  - via-ferrata
  - vtt
```