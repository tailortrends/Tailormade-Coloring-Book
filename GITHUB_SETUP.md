# GitHub Setup Guide

**Repository**: [tailortrends/Tailormade-Coloring-Book](https://github.com/tailortrends/Tailormade-Coloring-Book)

---

## Initial Setup (Completed)

The following setup has been completed:

```bash
# 1. Initialize git repository
git init

# 2. Add GitHub remote
git remote add origin https://github.com/tailortrends/Tailormade-Coloring-Book.git

# 3. Set main branch
git branch -M main
```

---

## Making Your First Commit

```bash
# 1. Check status
git status

# 2. Add all files (review .gitignore first!)
git add .

# 3. Create commit
git commit -m "Initial commit: B.L.A.S.T. Phases 0-2 complete

- Added Project Constitution (gemini.md)
- Created 8 architecture SOPs
- Completed Phase 1 research (GitHub, COPPA, WCAG, fal.ai, Firestore)
- Created API verification tools (Firebase, R2, fal.ai, Anthropic)
- Enhanced .gitignore for secrets protection"

# 4. Push to GitHub
git push -u origin main
```

---

## Daily Workflow

```bash
# Pull latest changes
git pull origin main

# Make changes, then stage and commit
git add .
git commit -m "Descriptive commit message"

# Push to GitHub
git push origin main
```

---

## Branch Strategy (Recommended)

For team collaboration:

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "Add your feature"

# Push feature branch
git push -u origin feature/your-feature-name

# Create Pull Request on GitHub
# After review and merge, delete branch
git checkout main
git pull origin main
git branch -d feature/your-feature-name
```

---

## Important Files Protected by .gitignore

The following files are **automatically excluded** from version control:

### Secrets (NEVER COMMIT THESE!)
- `backend/.env` — All API keys and credentials
- `*firebase-adminsdk*.json` — Firebase service account
- `frontend/.env.local` — Firebase public config (contains project IDs)

### Generated/Temporary Files
- `backend/.venv/` — Python virtual environment
- `frontend/node_modules/` — NPM dependencies
- `frontend/dist/` — Build output
- `.tmp/` — Temporary files
- `__pycache__/` — Python bytecode

### System Files
- `.DS_Store` — macOS metadata
- `.idea/` — JetBrains IDEs
- `.vscode/settings.json` — VS Code user settings

---

## Pre-Commit Checklist

Before committing, verify:

- [ ] No secrets in code (API keys, passwords, tokens)
- [ ] `.env` files not staged (`git status` should NOT show them)
- [ ] Firebase service account JSON not staged
- [ ] Code follows project conventions (see architecture SOPs)
- [ ] Run verification scripts if backend changed: `python tools/health_check.py`
- [ ] Frontend builds successfully: `cd frontend && pnpm build`
- [ ] Backend tests pass: `cd backend && uv run pytest`

---

## Commit Message Conventions

Use clear, descriptive commit messages:

### Format
```
<type>: <subject>

<optional body>

<optional footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (dependencies, build config)

### Examples
```bash
# Good commits
git commit -m "feat: add photo upload endpoint for Phase 2"
git commit -m "fix: correct rate limiting counter increment timing"
git commit -m "docs: update architecture SOP for image generation"

# Avoid vague commits
git commit -m "updates"  # ❌ Too vague
git commit -m "fix stuff"  # ❌ Not descriptive
```

---

## Collaboration Best Practices

### Pull Requests
1. Create feature branch from `main`
2. Make focused, atomic changes
3. Write clear PR description:
   - What changed
   - Why it changed
   - How to test
4. Reference issues if applicable: "Fixes #123"
5. Request review from team members

### Code Review
- Review architecture SOPs before approving backend changes
- Check that secrets are not exposed
- Verify tests are included for new features
- Ensure documentation is updated

---

## GitHub Actions (Future Phase 5)

When setting up CI/CD, include:

```yaml
# .github/workflows/ci.yml (example)
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Backend Tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest
      
      - name: Health Check
        env:
          FAL_KEY: ${{ secrets.FAL_KEY }}
        run: python tools/health_check.py
```

---

## Troubleshooting

### "Git push rejected"
```bash
# Pull latest changes first
git pull origin main --rebase
git push origin main
```

### "Accidentally committed secrets"
```bash
# Remove from history (CAREFUL!)
git rm --cached backend/.env
git commit -m "Remove accidentally committed secrets"
git push origin main --force

# Then rotate all API keys immediately!
```

### "Merge conflicts"
```bash
# Pull latest
git pull origin main

# Resolve conflicts in files
# Look for <<<<<<, ======, >>>>>> markers

# After resolving
git add .
git commit -m "Resolve merge conflicts"
git push origin main
```

---

## Related Documentation

- [README.md](README.md) — Project setup and quick start
- [gemini.md](gemini.md) — Project constitution and schemas
- [task_plan.md](task_plan.md) — B.L.A.S.T. phases and progress
- [.gitignore](.gitignore) — Files excluded from version control

---

**Last Updated**: 2026-02-12  
**Status**: Repository initialized and ready for first commit
