# Matseðillinn for Home Assistant

Shows the [Matseðillinn](https://matsedillinn.net) meal plan in Home Assistant: a calendar and sensors for today, tomorrow and the week.

## Installation

### HACS

1. HACS → ⋮ → **Custom repositories** → add `https://github.com/jongautur/matsedillinn-ha`, category **Integration**.
2. Install **Matseðillinn** and restart Home Assistant.

### Manually

Copy `custom_components/matsedillinn` into `config/custom_components/` and restart Home Assistant.

## Setup

**Settings → Devices & services → Add integration → Matseðillinn**, then paste one of the links from **Stillingar → Ytri tengingar** in Matseðillinn (or just the key after `?token=`).

If someone creates a new key in Matseðillinn, Home Assistant will ask for the new link.

## Entities

| Entity | State | Attributes |
| --- | --- | --- |
| `calendar.matsedillinn_meal_plan` | Today's dinner, or the next planned meal | One all-day event per meal |
| `sensor.matsedillinn_today` | Today's dinner (or first meal) | `date`, `date_label`, `meals` |
| `sensor.matsedillinn_tomorrow` | Tomorrow's dinner (or first meal) | `date`, `weekday`, `meals` |
| `sensor.matsedillinn_this_week` | Planned days, e.g. `5/7` | `markdown`, `next_week_markdown`, `days`, `week`, `from`, `to` |

Entity ids follow Home Assistant's language when the integration is added (in Icelandic e.g. `sensor.matsedillinn_i_dag`). Each meal in `meals` has `slot`, `slot_label`, `title`, `note`, `minutes`, `servings`, `image` and `url`.

The sensors' picture is the meal's image.

## Dashboard

```yaml
type: markdown
title: Matseðill vikunnar
content: "{{ state_attr('sensor.matsedillinn_this_week', 'markdown') }}"
```

```yaml
type: markdown
content: >
  {% set m = state_attr('sensor.matsedillinn_today', 'meals') %}
  ## {{ states('sensor.matsedillinn_today') }}
  {% if m and m[0].image %}![]({{ m[0].image }}){% endif %}
```

## Language

The language (Icelandic, English or Polish) is chosen during setup and can be changed under **Configure**.

## Development

```sh
uv venv -p 3.13 && uv pip install -r requirements_test.txt
.venv/bin/pytest
```
