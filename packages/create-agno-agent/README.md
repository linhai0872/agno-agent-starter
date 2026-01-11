# create-agno-agent

🚀 **Create a new Agno Agent project with a single command**

```bash
npx create-agno-agent my-project
```

## Features

- **Interactive Mode**: Select templates and configure your project step by step
- **Non-interactive Mode**: Use `--yes` for CI/CD or scripted setups
- **Template Selection**: Choose from GitHub Agent, Research Team, or Customer Workflow
- **Zero Git History**: Clean project without upstream git history

## Usage

```bash
# Interactive mode
npx create-agno-agent my-project

# Non-interactive with all templates
npx create-agno-agent my-project --yes

# Select a specific template
npx create-agno-agent my-project --template github-agent
```

## Templates

| Template            | Description                                      |
| ------------------- | ------------------------------------------------ |
| `github-agent`      | GitHub repository analyzer with memory and tools |
| `research-team`     | Multi-agent deep research coordination           |
| `customer-workflow` | Customer service workflow with RAG               |

## Development

```bash
# Install dependencies
npm install

# Build
npm run build

# Run tests
npm run test

# Watch mode for development
npm run dev
```

## License

MIT
