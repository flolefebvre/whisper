# Audio-to-Text Project Documentation

This file serves as the institutional memory for the audio-to-text project, ensuring continuity across context resets and different AI agent sessions.

## Project Overview

**Project Goal**: Create GPU-accelerated Python script to convert French M4A audio files to text using OpenAI Whisper
**Platform**: Ubuntu in WSL with CUDA support
**Critical Requirement**: MANDATORY GPU support - CPU processing not supported

## Task Management Protocol (CRITICAL)

### Master Task File Authority
- **tasks.md is the single source of truth** for all project status and progress
- This file is maintained in `/home/prezbar/dev/audio-to-text2/tasks.md`
- ALL team members (Project Manager, Senior Developer, Compliance Officer) MUST read and update this file

### Context Continuity Requirements

**MANDATORY FIRST ACTION for any AI agent:**
1. Always read `tasks.md` immediately when starting any work session
2. Check current project status, active tasks, and blockers
3. Understand what work has been completed and what's in progress
4. Update "Current Sprint Focus" section with planned work

**This protocol is CRITICAL because:**
- AI agents may experience context resets between sessions
- Project state must persist across different sessions and team members
- tasks.md contains 35+ tracked tasks with detailed acceptance criteria
- Without this protocol, work may be duplicated or project progress lost

### Task Update Responsibilities

**When starting work:**
- Mark tasks as "🔄 In Progress" 
- Update the "Current Sprint Focus" section
- Assign yourself to the task

**During work:**
- Update acceptance criteria checkboxes as completed: `[x]`
- Document any blockers or issues discovered
- Add notes about implementation decisions

**When completing work:**
- Mark all acceptance criteria as complete: `[x]`
- Change task status to "✅ Complete"
- Update progress counters in section headers
- Update overall dashboard progress percentages
- Document any new tasks discovered during implementation

**If blocked:**
- Change status to "🚫 Blocked"
- Document the specific blocker
- Add blocker details to "Current Sprint Focus"

### Workflow Standards

1. **No Work Without Reading tasks.md First**: This prevents duplicate work and ensures continuity
2. **Real-time Task Updates**: Update status immediately as work progresses
3. **Progress Preservation**: All progress tracking survives context resets
4. **Status Synchronization**: Any team member can understand current state by reading tasks.md

## Technical Architecture Decisions

### GPU Requirements (MANDATORY)
- Whisper MUST use GPU acceleration (CUDA)
- No CPU fallback supported
- GPU availability must be verified before processing
- Processing fails gracefully with clear error if GPU unavailable

### Project Scope
- **Single file processing only** (no batch processing)
- **Local-only processing** (no cloud APIs, standalone script)
- **French language optimization**
- **Plain text output** (no advanced formatting, timestamps, or special formatting)
- **No performance requirements specified** (focus on accuracy over speed)

### Development Environment
- Platform: Ubuntu in WSL (confirmed WSL environment)
- Python with virtual environment
- CUDA-compatible PyTorch
- Dependencies: openai-whisper, torch (GPU), torchaudio, pydub
- **No licensing constraints** for chosen tools and models

## Confirmed Requirements (From PM Q&A Session)

### Audio Input Specifications
- **Audio Quality**: Clear audio recordings expected (high-quality input)
- **Language**: French audio files (primary focus)
- **Format Priority**: M4A files (primary), with MP3/WAV support

### Performance & Hardware
- **Performance Requirements**: None specified (accuracy prioritized over speed)
- **GPU Requirement**: MANDATORY - base model default, GPU support required
- **Platform**: Ubuntu WSL environment confirmed

### Output Requirements
- **Output Format**: Plain text only (no timestamps, formatting, or advanced features)
- **Processing Mode**: Single file processing only (no batch operations)
- **Deployment**: Standalone local script (no API calls or cloud dependencies)

### User Experience Decisions
- **Model Selection**: Simple interface, no auto-suggestions based on hardware
- **Error Handling**: Clear messages without troubleshooting instructions
- **Caching**: Yes to model caching for efficiency
- **Licensing**: No constraints on tool/model selection

## User Preferences & Requirements

### Model Selection
- Simple user choice interface (command line)
- No auto-suggestions based on GPU memory
- Default to base model if none specified
- Models downloaded once and cached locally
- Available models: tiny, base, small, medium, large, large-v2, large-v3
- User provides simple model name selection (no complex configuration)

### Error Handling
- Error messages should be clear and concise
- Do NOT include troubleshooting steps in error output
- Focus on what went wrong, not how to fix it

### File Processing
- Support M4A primary format (PRIORITY: clear audio recordings expected)
- Expand to other audio formats (MP3, WAV)
- Single file workflow only (NO batch processing)
- Robust file validation and error handling
- Expected input: Clear, high-quality French audio recordings

## Project Dependencies & Task Flow

```
Foundation Tasks (1.1-1.4) → Core Functionality (2.1-2.4) → 
User Experience (3.1-3.4) + Configuration (4.1-4.3) → 
Advanced Features (5.1-5.3) + Testing (6.1-6.3) →
Documentation (7.1-7.3) + Infrastructure (8.1-8.3)
```

## Critical Success Factors

1. **GPU Environment Setup**: Must be completed first and verified working
2. **Task Tracking Discipline**: All agents must maintain tasks.md updates
3. **Context Preservation**: Use tasks.md to bridge context resets
4. **Requirements Adherence**: Single file, GPU-only, French optimization

## File Structure & Key Files

- `tasks.md`: Master task tracking file (35+ tasks with detailed acceptance criteria)
- `claude.md`: This institutional memory file
- `backlog.md`: Initial requirements (exists)
- Future: `requirements.txt`, main script, documentation

## Communication Protocol

When working across context resets or team member changes:
1. Read tasks.md first to understand current state
2. Update your planned work in "Current Sprint Focus"
3. Follow the task update protocol religiously
4. Document decisions and discoveries for future sessions
5. Maintain project continuity through consistent task tracking

This protocol ensures that the audio-to-text project maintains momentum and avoids work duplication regardless of context resets or different AI agents working on the project.