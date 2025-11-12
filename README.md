# Podcast Index MCP Server

An MCP (Model Context Protocol) server that provides access to the [Podcast Index](https://podcastindex.org/) API, enabling AI assistants to search and discover podcasts.

## Features

- **Comprehensive Search**: Search podcasts by general term, specific title, or episodes by person
- **Episode Discovery**: Browse all episodes from a podcast feed and get detailed episode information
- **Podcast Details**: Retrieve complete metadata including descriptions, funding, value blocks, and more
- **Rich Filtering**: Support for value block types (Lightning, Hive, WebMonetization), explicit content filtering, and date ranges
- **Secure Authentication**: Uses Podcast Index API key/secret authentication
- **Complete Workflows**: Enable multi-step discovery from search to detailed content exploration

## Prerequisites

- Python 3.10 or higher
- Podcast Index API credentials ([sign up here](https://api.podcastindex.org/signup))

## Installation

Choose the installation method that best fits your needs:

### Option 1: Quick Start with uvx (Recommended)

The fastest way to get started. No need to clone the repository:

```bash
uvx --from git+https://github.com/eugenechae/podcast-index-mcp podcast-index-mcp
```

**Pros**: One command install, automatic updates, no path configuration needed

**Requirements**: [uv](https://docs.astral.sh/uv/) package manager

### Option 2: Install with pipx

Install as a standalone tool using pipx:

```bash
pipx install git+https://github.com/eugenechae/podcast-index-mcp.git
```

**Pros**: Isolated environment, familiar to Python users, persistent installation

**Requirements**: [pipx](https://pipx.pypa.io/) (install with `pip install pipx`)

**To update**: `pipx upgrade podcast-index-mcp`

**To uninstall**: `pipx uninstall podcast-index-mcp`

### Option 3: Development Installation

For contributing or local development:

1. Clone the repository:
```bash
git clone https://github.com/eugenechae/podcast-index-mcp.git
cd podcast-index-mcp
```

2. Install dependencies:
```bash
uv sync
```

**Pros**: Full control, easy to modify and contribute

**Requirements**: [uv](https://docs.astral.sh/uv/) package manager

## Configuration

### Claude Desktop Setup

The configuration depends on your installation method. Add the appropriate configuration to your Claude Desktop configuration file:

**MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

#### For uvx Installation (Option 1)

```json
{
  "mcpServers": {
    "podcast-index": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/eugenechae/podcast-index-mcp",
        "podcast-index-mcp"
      ],
      "env": {
        "PODCAST_INDEX_API_KEY": "your-api-key-here",
        "PODCAST_INDEX_API_SECRET": "your-api-secret-here"
      }
    }
  }
}
```

**Note**: No path configuration needed! uvx handles everything automatically.

#### For pipx Installation (Option 2)

```json
{
  "mcpServers": {
    "podcast-index": {
      "command": "podcast-index-mcp",
      "env": {
        "PODCAST_INDEX_API_KEY": "your-api-key-here",
        "PODCAST_INDEX_API_SECRET": "your-api-secret-here"
      }
    }
  }
}
```

**Note**: The `podcast-index-mcp` command is available in your PATH after pipx installation.

#### For Development Installation (Option 3)

```json
{
  "mcpServers": {
    "podcast-index": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/podcast-index-mcp",
        "run",
        "podcast-index-mcp"
      ],
      "env": {
        "PODCAST_INDEX_API_KEY": "your-api-key-here",
        "PODCAST_INDEX_API_SECRET": "your-api-secret-here"
      }
    }
  }
}
```

**Important notes for development installation:**

1. **Get the absolute path** to the repository:
   - **MacOS/Linux**: Run `pwd` in the repository directory
   - **Windows**: Run `cd` in the repository directory

2. **Windows users**: Use double backslashes (`\\`) or forward slashes (`/`) in paths:
   ```
   "C:\\Users\\YourName\\podcast-index-mcp"
   ```
   Or alternatively:
   ```
   "C:/Users/YourName/podcast-index-mcp"
   ```

3. **If `uv` command is not found**, use the full path to the `uv` executable:
   - Find it with: `which uv` (MacOS/Linux) or `where uv` (Windows)
   - Example: `"command": "/Users/yourname/.local/bin/uv"`

### API Credentials

Replace `your-api-key-here` and `your-api-secret-here` with your actual Podcast Index API credentials. You can obtain these by [signing up here](https://api.podcastindex.org/signup).

## Usage

### Available Tools

#### search_podcasts

Search for podcasts by term across titles, authors, and owners in the Podcast Index database.

**Parameters:**
- `q` (string, required): Search query term
- `max` (integer): Maximum number of results (1-1000)
- `val` (string): Filter by value block type (`any`, `lightning`, `hive`, `webmonetization`)
- `clean` (boolean): Exclude explicit content
- `fulltext` (boolean): Return complete text fields instead of truncated
- `aponly` (boolean): Only return podcasts with iTunes IDs
- `similar` (boolean): Include similar matches

**Returns:**
Array of podcast feeds, each containing:
- `id`: Podcast Index feed ID
- `title`: Podcast title
- `author`: Podcast author/creator
- `description`: Podcast description (truncated unless `fulltext=true`)
- `url`: RSS feed URL
- Plus metadata like `image`, `link`, category information, and value block details if present

#### search_podcasts_by_title

Search for podcasts specifically by their title field (more focused than general search).

**Parameters:**
- `q` (string, required): Search term to match against podcast titles
- `max` (integer): Maximum number of results (1-1000)
- `val` (string): Filter by value block type
- `clean` (boolean): Exclude explicit content
- `fulltext` (boolean): Return complete text fields
- `similar` (boolean): Include similar title matches using fuzzy search

**Returns:**
Same structure as `search_podcasts` - array of podcast feeds with `id`, `title`, `author`, `description`, `url`, and additional metadata

#### search_episodes_by_person

Search for episodes featuring or mentioning a specific person.

**Parameters:**
- `q` (string, required): Person name to search for
- `max` (integer): Maximum number of episode results (1-1000)
- `fulltext` (boolean): Return complete episode descriptions

**Returns:**
Array of episodes, each containing:
- `id`: Episode ID
- `title`: Episode title
- `feedTitle`: Name of the podcast this episode belongs to
- `feedId`: Podcast Index feed ID
- `description`: Episode description (truncated unless `fulltext=true`)
- Plus additional metadata like `datePublished`, `link`, person tags, and other episode details

#### get_episodes

Retrieve all episodes from a specific podcast feed in reverse chronological order.

**Parameters:**
- `id` (integer, required): Podcast feed ID from Podcast Index
- `since` (integer): Unix timestamp - only return episodes published after this time
- `max` (integer): Maximum number of episodes (1-1000)
- `fulltext` (boolean): Return complete episode descriptions

**Returns:**
Array of episodes from the specified podcast feed, each containing:
- `id`: Episode ID
- `title`: Episode title
- `description`: Episode description (truncated unless `fulltext=true`)
- `datePublished`: Unix timestamp of publication date
- Plus metadata like `link`, `enclosureUrl`, `duration`, chapters, transcripts, and other episode details

#### get_podcast_details

Get complete metadata for a specific podcast by feed ID.

**Parameters:**
- `id` (integer, required): Podcast feed ID from Podcast Index

**Returns:**
Complete podcast feed metadata, including:
- `id`: Podcast Index feed ID
- `title`: Podcast title
- `author`: Podcast author/creator
- `description`: Full podcast description
- `url`: RSS feed URL
- `link`: Podcast website
- `image`: Podcast artwork URL
- Plus comprehensive metadata like categories, funding information, value blocks, iTunes data, and language

#### get_episode_details

Get complete metadata for a specific episode by episode ID.

**Parameters:**
- `id` (integer, required): Episode ID from Podcast Index
- `fulltext` (boolean): Return complete episode description

**Returns:**
Complete episode metadata, including:
- `id`: Episode ID
- `title`: Episode title
- `feedTitle`: Name of the podcast
- `feedId`: Podcast Index feed ID
- `description`: Episode description (truncated unless `fulltext=true`)
- `link`: Episode URL
- Plus detailed metadata like person tags, chapters, transcripts, soundbites, value blocks, and publication date

### Example Workflows

These multi-tool workflows demonstrate the power of combining different endpoints:

#### 1. Person-Centric Discovery
```
"Find episodes featuring Jensen Huang, then show me complete details about the first result,
including information about the podcast it's from."
```
Tools used: `search_episodes_by_person` → `get_episode_details` → `get_podcast_details`

#### 2. Topic Deep Dive
```
"Search for podcasts about artificial intelligence, get the details of the top result,
and show me its 10 most recent episodes."
```
Tools used: `search_podcasts` → `get_podcast_details` → `get_episodes`

#### 3. Lightning-Enabled Content Search
```
"Find podcasts that support Bitcoin Lightning payments, get details on the first 3 results,
and show me their latest episodes."
```
Tools used: `search_podcasts` (with val='lightning') → `get_podcast_details` (×3) → `get_episodes` (×3)

#### 4. Comparative Analysis
```
"Search for 'technology news' podcasts, compare the top 2 by getting their full details,
and show me the 5 most recent episodes from each."
```
Tools used: `search_podcasts` → `get_podcast_details` (×2) → `get_episodes` (×2)

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=podcast_index

# Run specific test file
uv run pytest tests/test_client.py
```

### Code Quality

```bash
# Type checking
uv run pyrefly check

# Linting
uv run ruff check .

# Formatting
uv run ruff format .
```

### Running the Server Locally

For development installations (Option 3), you can run the server directly:

```bash
# Run via Python module
uv run python -m podcast_index.main

# Or use the entry point command
uv run podcast-index-mcp
```

The server uses stdio transport and communicates via the MCP protocol.

For uvx or pipx installations, the server runs automatically when configured in Claude Desktop - no need to run it manually.

## API Documentation

For detailed API documentation, visit the [Podcast Index API docs](https://podcastindex-org.github.io/docs-api/).

## License

MIT License - see LICENSE file for details

## Acknowledgments

- [Podcast Index](https://podcastindex.org/) for providing the API
- [Model Context Protocol](https://modelcontextprotocol.io/) for the MCP specification
