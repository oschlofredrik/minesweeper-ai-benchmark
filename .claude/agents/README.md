# Claude Code Sub-Agents for Tilts Platform

This directory contains specialized sub-agents that can be invoked by the main Claude Code agent to handle specific tasks related to the Tilts platform.

## Available Sub-Agents

### 1. benchmark-analyzer
**Purpose**: Analyzes benchmark results and provides insights on model performance.

**Capabilities**:
- Statistical analysis of game results
- Performance comparisons between models
- Trend identification
- Report generation

**Usage**: Invoked when analyzing evaluation results or comparing model performance.

### 2. game-implementer
**Purpose**: Implements new games for the platform following the established plugin architecture.

**Capabilities**:
- Creates game logic following base interfaces
- Implements AI-friendly board representations
- Designs function calling schemas
- Creates test scenarios

**Usage**: Invoked when adding new games to the platform.

### 3. performance-optimizer
**Purpose**: Optimizes code performance for serverless environments.

**Capabilities**:
- Identifies performance bottlenecks
- Optimizes cold starts
- Reduces bundle sizes
- Improves caching strategies

**Usage**: Invoked when dealing with performance issues or optimization needs.

### 4. debug-assistant
**Purpose**: Semi-automated debugging specialist for Vercel deployments.

**Capabilities**:
- Uses Vercel CLI for deployment analysis
- Automated error pattern detection
- Creates debug scripts and reports
- Monitors function execution

**Usage**: Invoked when debugging deployment issues or API errors.

## How Sub-Agents Work

1. **Invocation**: The main agent uses the Task tool to invoke a sub-agent
2. **Context**: The sub-agent receives specific context about the task
3. **Execution**: The sub-agent performs its specialized work
4. **Results**: Returns results to the main agent for integration

## Adding New Sub-Agents

To add a new sub-agent:

1. Create a new `.md` file in this directory
2. Follow the frontmatter format:
   ```yaml
   ---
   name: agent-name
   description: Brief description of the agent's purpose
   tools: List, of, tools, the, agent, needs
   ---
   ```
3. Document the agent's responsibilities and capabilities
4. Include specific workflows and examples

## Integration with Debugging Scripts

The debug-assistant sub-agent works with the automated scripts in `/scripts/`:
- `debug-vercel.py`: Comprehensive diagnostic tool
- `monitor-functions.sh`: Real-time function monitoring
- `test-ai-endpoints.py`: AI integration testing
- `quick-debug.sh`: Quick issue detection

These scripts can be run independently or invoked by the debug-assistant for systematic troubleshooting.