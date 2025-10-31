# Podcast Index MCP Server

An MCP (Model Context Protocol) server that provides access to the [Podcast Index](https://podcastindex.org/) API, enabling AI assistants to search and discover podcasts.

## Features

- **Search Podcasts**: Search for podcasts by term across titles, authors, and owners
- **Rich Filtering**: Support for various filters including explicit content filtering, value block types, and more
- **Secure Authentication**: Uses Podcast Index API key/secret authentication
- **Extensible Design**: Built with clean architecture for easy addition of more endpoints

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

Search for podcasts by term across the Podcast Index database.

**Required Parameters:**
- `q` (string): Search query term

**Optional Parameters:**
- `max` (integer): Maximum number of results (1-1000)
- `val` (string): Filter by value block type (`any`, `lightning`, `hive`, `webmonetization`)
- `clean` (boolean): Exclude explicit content
- `fulltext` (boolean): Return complete text fields instead of truncated
- `aponly` (boolean): Only return podcasts with iTunes IDs
- `similar` (boolean): Include similar matches

**Example Queries:**
- "Search for Python programming podcasts"
- "Find clean podcasts about technology"
- "Search for podcasts with Lightning value enabled"

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
