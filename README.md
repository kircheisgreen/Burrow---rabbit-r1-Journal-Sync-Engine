# Burrow - rabbit r1 Journal Sync Engine

Burrow collects Rabbit Hole journals or Rabbit-generated Gmail messages, transforms each journal into structured notes, and uploads the results to Google Drive.

The supported GUI entry point is `main.py`. The application is a Windows Tkinter desktop tool. Background automation uses Windows Task Scheduler.

## What The App Does

- Fetches journals from Rabbit Hole or Gmail.
- Extracts journal titles, dates, HTML content, speakers, and transcript metadata.
- Uploads every journal `<img src="...">` image into the current journal Drive folder.
- Creates Cornell, Outlining, Mind Mapping, and Boxing versions.
- Uploads Google Docs, Markdown, and PDF documents.
- Creates PNG, SVG, or PDF Mind Mapping visualizations.
- Saves named configuration profiles.
- Avoids duplicate sync work using local history and optional Drive checksums.
- Runs scheduled fetch-and-sync cycles through Windows Task Scheduler.

## Requirements

- Windows with Python 3.14 or a compatible supported Python version.
- Tkinter, normally included with the Windows Python installer.
- A Google Cloud OAuth desktop client for Drive and Docs. Gmail access is also required when Gmail is selected as the source.
- A logged-in Windows desktop session for visible scheduled Chromium execution.
- Chromium installed for Playwright.

## Installation

From the project directory:

```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Use the same Python interpreter for installation and execution. Verify the important packages with:

```powershell
python -c "import googleapiclient, matplotlib, playwright, reportlab; print('dependencies ok')"
```

Start the application:

```powershell
python main.py
```

### Building `main.exe`

Build from the same virtual environment used to install the application:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH = "0"
python -m playwright install chromium
pyinstaller --clean --noconfirm main.spec
```

`PLAYWRIGHT_BROWSERS_PATH=0` installs Chromium inside the Playwright package so `main.spec` can bundle it into the executable distribution. The build stops with a clear error if Chromium has not been installed first. Distribute the complete `dist/main/` directory, not only `main.exe`, because the onedir build stores Python libraries and Chromium under `_internal/`.

## Google Cloud Setup

1. Open [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a project.
3. Enable Google Drive API, Google Docs API, and Gmail API.
4. Configure the OAuth consent screen and add your account as a test user when using an External app.
5. Create an OAuth client ID with application type **Desktop app**.
6. Download the client JSON and place it in the project root as `credentials.json`.

`credentials.json` is the application client configuration. It is not a user token and cannot be generated automatically by this app. After the first Google authorization, `token.json` stores the access/refresh token used by later runs.

## The Main Window

### User Profile Setup Manager

- **Active Profile** selects a named configuration.
- **Save Current Config** stores the current controls in `rabbit_sync_profiles.json`.

Profiles include source, credentials path, Rabbit credentials, Drive folder, framework selections, output formats, deduplication, and scheduler settings.

### 1. Input Data Source Settings

Choose one source:

- **Rabbit Hole**: uses the persistent Chromium profile in `browser_session/`, navigates to `https://hole.rabbit.tech/journal/details`, and writes scraped journals to `rabbit_journals_dump.json`.
- **Google Mail**: searches Gmail messages from `rabbit@r1.rabbit.tech` and extracts plain text or HTML message content.

For Rabbit Hole, enter the Rabbit username/email and password when needed. The **Programmatic Auto-Fetch Journals (Headless Routing)** button launches the crawler. In the current modular GUI, the normal button uses the visible browser flow; scheduled automation also uses visible Chromium so it can work with the interactive authenticated session.

**Only Unfetched Dates** skips date containers whose normalized date already appears as `createdAt` in `rabbit_journals_dump.json`. The crawler also uses SHA-256 card fingerprints and skips matching cached cards. Leave this unchecked to scan all discovered dates.

Maintenance controls are also available under this section:

- **Clear Cache** deletes `rabbit_journals_dump.json` and `sync_history.json`.
- **Clear Session** deletes the `browser_session/` Chromium profile directory. Close Chromium first; Windows may refuse to remove files that are still locked.
- **Clear Log** deletes `sync_service.log`.

These actions are permanent and run in the background. The GUI log reports each deletion or any file-lock/permission failure.

After a fetch, choose the post-fetch action:

- **Manual Sync**: stop after fetching.
- **Run Sync After Fetch**: start the normal sync.
- **Run Force Override Sync**: start sync with history checks bypassed.

Rabbit scraping depends on the current Rabbit Hole page structure and Cloudflare/session state. A login page or `ERROR: The request could not be satisfied` page contains no journal cards to scrape.

### 2. Note-Taking Frameworks

Sections 2, 3, and 4 are collapsible. Use the `-`/`+` control in each section header to expand or compact its settings. Section 2 is open by default; sections 3 and 4 start collapsed to reduce the initial window height on lower-resolution screens.

Select any combination of:

- **Cornell Method**
- **Outlining**
- **Mind Mapping**
- **Boxing**

Each selected framework produces an additional journal output. The current implementation places outputs in the selected Drive lecturer/date folders; it does not create separate workflow subfolders.

### 3. Google Drive Settings

- Enter or browse for the `credentials.json` path.
- Load Drive folders to populate the folder selector.
- Select the destination parent folder. The default is the Drive root.

The sync engine organizes files under:

```text
Selected parent folder/
  Lecturer/
    YYYY-MM-DD/
      Journal type/
        Journal outputs
```

For Rabbit Hole journals, each date container's descendant `svg[aria-label]` value becomes the name of a subfolder under the lecturer/date folder. The journal document, framework documents, and Mind Mapping visualization for that container are uploaded into that subfolder. Sources without this metadata continue to use the date folder directly.

### 4. Automation Cron Background Task Settings

Enable **Enable Background Automation Service Routine Flow Loop Run** to show scheduler controls. Choose:

- **Daily** with a time of day.
- **Hourly** with a recurrence value.
- **Minute** with a recurrence value such as `1`.

Click **Save Automation Task Registry** to generate `run_background_sync.bat` and register `RabbitR1_GoogleDocs_Sync` with Windows Task Scheduler.

Each scheduled run performs two phases:

1. **Programmatic Auto-Fetch Journals**: loads the active profile credentials, opens the persistent Chromium profile, navigates to Rabbit Hole, and refreshes the local journal cache.
2. **Start Sync Process**: uploads the selected source using normal history-aware sync (`force_sync=False`). Scheduled automation does not use Force Override Sync All.

The task uses the logged-in interactive Windows user. Keep that session available because visible Chromium mode cannot run as a hidden service. Task Scheduler is configured to ignore a new trigger while an earlier run is still active.

Click **Disable Background Automation Service** to remove the registered task, delete the generated batch launcher, uncheck the background-service control, and hide the scheduler controls.

### 5. Output Preferences

#### Doc Format

- **Google Doc**: creates a native Google Doc or clears and rewrites the existing document.
- **Markdown**: uploads a `.md` file.
- **PDF**: converts the parsed HTML into a styled `.pdf` file.

The HTML parser removes sidebars and buttons, preserves speaker styling, and converts `ml:hidden` elements to a space so adjacent words do not run together. PDF document output embeds a Unicode-capable Windows font for box-drawing characters.

Images embedded in journal HTML are uploaded separately to the same current journal folder. HTTP(S) image URLs and data URLs are supported. Image names use the journal title and an image index, for example `Journal_Title_image_01.png`.

#### Mind Mapping Image Format

When Mind Mapping is selected:

- **PNG** creates a Matplotlib raster visualization.
- **SVG** creates a vector SVG visualization.
- **PDF** creates a vector PDF visualization.

Visualization names include `MindMap Visualization`, distinct from the `MindMapping` document name.

#### Dedup Profiles Content

Deduplication uses the generated content checksum where supported. Markdown and PDF uploads compare a local MD5 checksum with Drive metadata. Existing Google Docs are rewritten rather than checksum-skipped. Sync history also prevents normal sync from processing the same journal configuration repeatedly.

Use **Start Sync Process** for normal history-aware synchronization. Use **Force Override Sync All** to bypass sync history and process all journals again.

## Google Authorization

The first Google Drive, Docs, or Gmail operation opens an OAuth consent flow. Grant the requested scopes and complete the browser flow. The result is cached in `token.json`.

If Google returns `403 insufficientPermissions`, delete or renew `token.json` and authorize the required Drive, Docs, and Gmail scopes again.

## Rabbit Authentication And Cloudflare

The crawler reuses `browser_session/` as a persistent Chromium profile. It can populate the Rabbit login form from the active profile, detect the **Verify you are human** control in the page or an iframe, and log the frame URLs it sees.

Cloudflare may still require manual interaction. These messages indicate an upstream login/challenge problem, not a CSS selector problem:

```text
ERROR: The request could not be satisfied
ERR_NAME_NOT_RESOLVED
```

If the crawler reaches the login page but cannot proceed, confirm the profile has a valid authenticated session and that the Cloudflare challenge can load in the current network.

## Logs And Diagnostics

### GUI log

The bottom console shows interactive progress messages.

### `sync_service.log`

This is the primary scheduled-run log. A healthy scheduled cycle includes markers like:

```text
BACKGROUND PHASE 1/2 START: Programmatic Auto-Fetch Journals
BACKGROUND PHASE 1/2 END: Auto-fetch returned ...
BACKGROUND PHASE 2/2 START: Start Sync Process
BACKGROUND PHASE 2/2 END: Start Sync Process completed successfully ...
```

Crawler diagnostics include the current URL/title, selector counts, mapped cards, skipped dates, and page-crash messages.

The log rolls over at midnight. Before a new `sync_service.log` is opened, the previous log is compressed into a dated archive such as `sync_service.2026-08-24.zip`. Archives older than the profile's `log_retention_days` value are removed. The default retention is 7 days; this value is stored in `rabbit_sync_profiles.json` and defaults to 7 for profiles created by older versions.

### `background_crash.log`

Captures output and errors from the generated batch launcher. `^C` means the process was interrupted. An empty or newline-only file does not by itself indicate a sync failure; inspect `sync_service.log` for the phase result.

### Task Scheduler commands

```powershell
schtasks.exe /Query /TN "RabbitR1_GoogleDocs_Sync" /V /FO LIST
schtasks.exe /Run /TN "RabbitR1_GoogleDocs_Sync"
```

For a one-minute schedule, the query should show a minute repetition similar to:

```text
Schedule Type: One Time Only, Minute
Repeat: Every: 0 Hour(s), 1 Minute(s)
```

## Troubleshooting

- **No new journals**: inspect the crawler URL/title. A login or error page has no journal DOM. If cards are found but skipped, check `Only Unfetched Dates` and the cache's `createdAt` values.
- **Human verification is not clicked**: confirm the challenge loaded. A failed Cloudflare challenge may expose no checkbox or iframe.
- **The scheduled task does not trigger**: query the task, confirm it is enabled, confirm the next run time, and keep the interactive Windows user session logged in.
- **The task stays running**: a browser fetch and Drive sync can take longer than one interval. Overlapping triggers are ignored.
- **The GUI freezes during task registration**: registration and removal run on worker threads and use bounded `schtasks.exe` calls. Check `sync_service.log` for the returned scheduler error.
- **Google Drive rejects uploads**: refresh OAuth authorization and confirm Drive/Docs scopes.
- **PDF shows black squares**: regenerate the PDF after updating the app. Current PDF output embeds Arial with Unicode mappings for box-drawing characters.
- **PDF words run together**: the parser replaces `ml:hidden` content with a space; regenerate the document with the current version.
- **A generated file appears duplicated**: document and visualization names are intentionally different. A Mind Mapping document uses `MindMapping`; its visualization uses `MindMap Visualization`.

## Data Files

| File | Purpose |
| --- | --- |
| `credentials.json` | Google OAuth client configuration. |
| `token.json` | Google OAuth access/refresh token cache. |
| `rabbit_sync_profiles.json` | Named profiles, including Rabbit credentials. |
| `rabbit_journals_dump.json` | Local Rabbit journal cache and scraper fingerprints. |
| `sync_history.json` | Normal-sync history fingerprints. |
| `run_background_sync.bat` | Generated Task Scheduler launcher. |
| `sync_service.log` | Structured application and scheduled-service log. |
| `background_crash.log` | Generated batch output/error capture. |
| `browser_session/` | Persistent Chromium cookies and browser state. |

Do not edit or delete these files while a fetch or sync is running.

## Security

This app handles private journals and authentication material:

- Never commit `credentials.json`, `token.json`, `rabbit_sync_profiles.json`, `rabbit_journals_dump.json`, `sync_history.json`, `browser_session/`, generated batch files, or logs.
- The repository `.gitignore` currently ignores only `__pycache__/`; add sensitive files before using git or sharing the project.
- Rabbit passwords are stored in plaintext in profile JSON.
- Generated scheduler batch files can contain access tokens and local paths.
- Rotate or revoke credentials if sensitive files have been shared.

## Developer Commands

Run the current tests:

```powershell
python -m unittest discover -s tests -v
```

The current test suite contains an unrelated stale assertion expecting `CENTRAL IDEA` while the transformer emits `CENTRAL TOPIC`.

The main implementation areas are:

- `rabbit_sync/components/`: GUI panels.
- `rabbit_sync/gui_handlers.py`: GUI actions and worker threads.
- `rabbit_sync/auth_crawler.py`, `crawler_navigation.py`, `crawler_scraper.py`: Rabbit browser fetch.
- `rabbit_sync/sync_engine.py`: transformation and upload orchestration.
- `rabbit_sync/uploader*.py`: Google Doc, Markdown, PDF, and HTML conversion.
- `rabbit_sync/visualizer.py`: SVG, PNG, and PDF mind maps.
- `rabbit_sync/windows_task_registrar.py`, `scheduler_cli.py`: background automation.

