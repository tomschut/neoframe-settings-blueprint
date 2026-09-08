# NeoFrame Settings Blueprint

A Home Assistant automation blueprint: serves the remote settings JSON that
a [NeoFrame](https://github.com/tomschut/neoframe) e-paper photo frame polls
for its cron-style wake schedule, timezone, power profile, and `paused`
flag. Home Assistant becomes the single place that schedule and pause state
live, instead of hand-editing JSON on NeoFrame's own `/schedule` page.

Unlike the [pause/resume blueprint](https://github.com/tomschut/neoframe-pause-automation-blueprint),
which calls NeoFrame's `/pause` and `/resume` endpoints directly (light
sleep, WiFi stays up), this one drives NeoFrame's newer `low_power`/`ac_power`
schedule engine (see the main repo's README, "Scheduled deep sleep")
through the `config_url` it already polls on its own - nothing calls
*into* Home Assistant here, NeoFrame calls *out* to it.

## No extra setup required

Unlike the pause/resume blueprint, this one needs no `rest_command:` in
`configuration.yaml` - a webhook trigger with a response is a built-in
Home Assistant automation feature (Core 2024.6+).

## Import the blueprint

In Home Assistant: **Settings → Automations & Scenes → Blueprints → Import
Blueprint**, and paste:

```
https://github.com/tomschut/neoframe-settings-blueprint/blob/master/neoframe_settings.yaml
```

Then create a new automation from the imported blueprint and fill in:

- **Image URL** - full URL NeoFrame should render, e.g.
  `http://192.168.1.10:8000/frame`.
- **Timezone** - a POSIX TZ rule. `Europe/Amsterdam` and `UTC` are
  recognized as friendly names; anything else needs the raw POSIX rule
  (e.g. `CET-1CEST,M3.5.0,M10.5.0/3`).
- **Power profile** - `low_power` (deep sleeps between windows, battery use),
  `ac_power` (same schedule, never sleeps, settings page always reachable,
  mains-powered use), or `always_on` (ignores the schedule entirely).
- **Schedule** - a list of wake windows, e.g.:
  ```yaml
  - days: mon-fri
    start: "08:00"
    stop: "22:00"
    every: "5m"
  - days: sat-sun
    start: "10:00"
    stop: "23:00"
    every: "10m"
  ```
- **Paused-when-not source entity** - a `binary_sensor`, `group`, or
  `input_boolean` whose state decides NeoFrame's `paused` flag. You can
  point this at the exact same presence entity the pause/resume blueprint
  uses.
- **"Active" state** - the state of that entity meaning NeoFrame should be
  active (not paused); anything else pauses it. Default `on`.

Save the automation, open it, click the webhook trigger, and copy its URL
(**Copy URL** button) - it looks like
`http://<your-ha-host>:8123/api/webhook/<random-id>`.

## Point NeoFrame at it

On NeoFrame's always-on settings page (`http://<device-ip>/`), set
**Settings URL** to the webhook URL you copied, and save. NeoFrame will
start polling it on its own schedule (or immediately, via "Force reload
now"/serial `force`).

## What it returns

A plain `200` JSON response on every request, e.g.:

```json
{
  "timezone": "Europe/Amsterdam",
  "power_profile": "low_power",
  "image_url": "http://192.168.1.10:8000/frame",
  "schedule": [
    {"days": "mon-fri", "start": "08:00", "stop": "22:00", "every": "5m"}
  ],
  "paused": false
}
```

There's no `ETag`/`Last-Modified`, so NeoFrame never gets a `304` from this
endpoint - it always re-parses the full response. That's fine: NeoFrame
already compares the parsed result against its current configuration and
skips the flash write when nothing changed, so this doesn't cost extra
flash wear, just a slightly larger poll response.

The webhook is marked `local_only`, so it only answers requests reaching
Home Assistant over your LAN - matching NeoFrame's own settings page trust
model (unauthenticated, reachable to anything already on your network).
