# Tilts Monorepo Structure

This project has been restructured as a monorepo using npm workspaces.

## Structure

```
tilts/
├── packages/
│   ├── api/          # Python API handlers and TypeScript AI integration
│   ├── web/          # Frontend static files (HTML, CSS, JS)
│   └── shared/       # Shared TypeScript types and utilities
├── package.json      # Root workspace configuration
├── tsconfig.base.json # Shared TypeScript configuration
└── vercel.json       # Vercel deployment configuration
```

## Packages

### @tilts/api
- Python API handlers for Vercel
- TypeScript AI integration using Vercel AI SDK
- Game evaluation and streaming endpoints

### @tilts/web
- Static frontend files
- Game visualizations and UI components
- No build process needed (vanilla JS)

### @tilts/shared
- Shared TypeScript types (GameType, ModelConfig, etc.)
- Common utilities (validation, formatting)
- Used by both API and future TypeScript packages

## Development

```bash
# Install dependencies for all packages
npm install

# Run type checking across all packages
npm run type-check

# Run development server
npm run dev
```

## Key Changes from Previous Structure

1. **Unified Path Structure**: All packages under `/packages/`
2. **Shared Types**: Common types extracted to `@tilts/shared`
3. **Updated Imports**: TypeScript files now import from `@tilts/shared`
4. **Static File Paths**: Python handlers updated to serve from `packages/web/`
5. **Vercel Routes**: Updated to point to new package locations

## Adding New Packages

To add a new package:

1. Create directory under `packages/`
2. Add `package.json` with name `@tilts/[package-name]`
3. Add to root `tsconfig.json` references if TypeScript
4. Update `vercel.json` if needed for deployment

## Benefits

- **Type Safety**: Shared types ensure consistency
- **Modularity**: Clear separation of concerns
- **Scalability**: Easy to add new packages
- **Dependency Management**: Workspace handles cross-package dependencies
- **Build Optimization**: Each package can have its own build process