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

- Python 3.10.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- Podcast Index API credentials ([sign up here](https://api.podcastindex.org/))

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd podcast-index-mcp
```

2. Install dependencies:
```bash
uv sync
```

## Configuration

### Claude Desktop Setup

To use this MCP server with Claude Desktop, add the following to your Claude Desktop configuration file:

**MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "podcast-index": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/podcast-index-mcp",
        "run",
        "python",
        "-m",
        "main"
      ],
      "env": {
        "PODCAST_INDEX_API_KEY": "your-api-key-here",
        "PODCAST_INDEX_API_SECRET": "your-api-secret-here"
      }
    }
  }
}
```

Replace `/absolute/path/to/podcast-index-mcp` with the actual path to this repository.

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

#### search_podcasts_by_title

Search for podcasts specifically by their title field (more focused than general search).

**Parameters:**
- `q` (string, required): Search term to match against podcast titles
- `max` (integer): Maximum number of results (1-1000)
- `val` (string): Filter by value block type
- `clean` (boolean): Exclude explicit content
- `fulltext` (boolean): Return complete text fields
- `similar` (boolean): Include similar title matches using fuzzy search

#### search_episodes_by_person

Search for episodes featuring or mentioning a specific person.

**Parameters:**
- `q` (string, required): Person name to search for
- `max` (integer): Maximum number of episode results (1-1000)
- `fulltext` (boolean): Return complete episode descriptions

#### get_episodes

Retrieve all episodes from a specific podcast feed in reverse chronological order.

**Parameters:**
- `id` (integer, required): Podcast feed ID from Podcast Index
- `since` (integer): Unix timestamp - only return episodes published after this time
- `max` (integer): Maximum number of episodes (1-1000)
- `fulltext` (boolean): Return complete episode descriptions

#### get_podcast_details

Get complete metadata for a specific podcast by feed ID.

**Parameters:**
- `id` (integer, required): Podcast feed ID from Podcast Index

#### get_episode_details

Get complete metadata for a specific episode by episode ID.

**Parameters:**
- `id` (integer, required): Episode ID from Podcast Index
- `fulltext` (boolean): Return complete episode description

### Example Workflows

These multi-tool workflows demonstrate the power of combining different endpoints:

#### 1. Person-Centric Discovery
```
"Find episodes featuring Adam Curry, then show me complete details about the first result,
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

```bash
# Run the MCP server
PYTHONPATH=src uv run python -m main
```

The server uses stdio transport and communicates via the MCP protocol.

## Project Structure

```
podcast-index-mcp/
├── src/
│   ├── main.py                 # MCP server implementation
│   └── podcast_index/
│       ├── __init__.py
│       ├── auth.py            # Authentication utilities
│       └── client.py          # API client
├── tests/
│   ├── test_auth.py           # Authentication tests
│   ├── test_client.py         # API client tests
│   └── test_server.py         # MCP server tests
├── pyproject.toml             # Project configuration
└── README.md
```

## API Documentation

For detailed API documentation, visit the [Podcast Index API docs](https://podcastindex-org.github.io/docs-api/).

## Contributing

Contributions are welcome! Please ensure:

1. All tests pass: `uv run pytest`
2. Code is formatted: `uv run ruff format .`
3. Linting passes: `uv run ruff check .`
4. Type checking passes: `uv run pyrefly check`

## License

MIT License - see LICENSE file for details

## Acknowledgments

- [Podcast Index](https://podcastindex.org/) for providing the API
- [Model Context Protocol](https://modelcontextprotocol.io/) for the MCP specification
