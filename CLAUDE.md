Welcome to the NeuroApp project workspace!
This file defines strict architectural, stylistic, and execution rules for NeuroApp development.

## 1. Execution & Orchestration
- Explore → Plan → Code: Always map out the step-by-step architecture using `<thinking>` tags before making code changes.
- Incremental Execution: The project is divided into phases. Check `progress.txt` to see current progress. Do not start a new phase until explicitly instructed.
- Context Management: If the context window gets heavy, pause work, update `progress.txt`, and advise to run `/compact`.

## 2. Verification First (Test-Driven)
- Before writing any core algorithmic logic in `backend/app/analyzers/`, you must write thorough unit tests in `backend/tests/`.
- Run tests regularly using:
  ```bash
  pytest backend/tests/
  ```
- Always fix root causes. Do not suppress errors.

## 3. Aesthetic & Accessibility Standards (Frontend Phase 2+)
- Museum-Quality Craftsmanship: The UI must be pristine. No "AI slop" gradients or unnecessary centered layouts. Keep it professional.
- Typography: Minimum 16px body font size. Use **Poppins** for headings and **Inter** or **Source Sans Pro** for body text.
- WCAG 2.1 Compliance: Target contrast ratio of strictly 7:1 for all colors, especially the Transcript View color-codings (Red/High, Yellow/Medium, Green/Low). Ensure keyboard navigation and semantic ARIA labeling.

## 4. Tech Stack Overview
- **Backend:** Python, FastAPI, Whisper, PostgreSQL + TimescaleDB.
- **Frontend:** Electron, React 18, TypeScript, Tailwind CSS, shadcn/ui, Zustand.
- **AI Core:** GPT-4o / Claude 3.5 Sonnet, Wav2Vec2, Praat/Parselmouth.
