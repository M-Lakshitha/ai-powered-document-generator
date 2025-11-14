from fastapi import APIRouter, HTTPException, BackgroundTasks
from pathlib import Path
import asyncio
from typing import Dict
from backend.config import settings
from backend.models.schemas import GenerationRequest, GenerationStatus, GenerationResult, TaskStatus
from backend.services.chunker import chunker
from agents.coordinator import AgentCoordinator

router = APIRouter()

# Track generation tasks (use Redis in production)
generation_tasks = {}

@router.post("/", response_model=GenerationStatus)
async def generate_documentation(
    request: GenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    Start documentation generation for uploaded files
    Returns immediately with task status, generation runs in background
    """
    from backend.routes.upload import active_sessions
    
    # Validate session exists
    if request.session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found. Please upload files first.")
    
    # Check if already generating
    if request.session_id in generation_tasks:
        task = generation_tasks[request.session_id]
        if task["status"] in [TaskStatus.PROCESSING, TaskStatus.ANALYZING]:
            raise HTTPException(status_code=409, detail="Documentation generation already in progress")
    
    # Initialize task status
    generation_tasks[request.session_id] = {
        "status": TaskStatus.PENDING,
        "progress": 0,
        "current_stage": "Initializing",
        "message": "Starting documentation generation...",
        "files_processed": 0,
        "total_files": len(active_sessions[request.session_id]["files"])
    }
    
    # Start background task
    background_tasks.add_task(
        _generate_docs_background,
        request.session_id,
        request.project_name,
        request.include_examples
    )
    
    print(f"🚀 Generation started for session: {request.session_id}")
    return GenerationStatus(
        session_id=request.session_id,
        status=TaskStatus.PENDING,
        progress=0,
        current_stage="Initializing",
        message="Documentation generation started",
        files_processed=0,
        total_files=generation_tasks[request.session_id]["total_files"]
    )

@router.get("/status/{session_id}", response_model=GenerationStatus)
async def get_generation_status(session_id: str):
    """Get current status of documentation generation"""
    if session_id not in generation_tasks:
        raise HTTPException(status_code=404, detail="Generation task not found")
    
    task = generation_tasks[session_id]
    return GenerationStatus(
        session_id=session_id,
        status=task["status"],
        progress=task["progress"],
        current_stage=task["current_stage"],
        message=task["message"],
        files_processed=task["files_processed"],
        total_files=task["total_files"],
        estimated_time_remaining=task.get("estimated_time")
    )

@router.get("/result/{session_id}", response_model=GenerationResult)
async def get_generation_result(session_id: str):
    """Get final result and download links"""
    if session_id not in generation_tasks:
        raise HTTPException(status_code=404, detail="Generation task not found")
    
    task = generation_tasks[session_id]
    if task["status"] != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail=f"Generation not complete. Current status: {task['status']}"
        )
    
    return GenerationResult(
        session_id=session_id,
        status=task["status"],
        files_generated=task.get("files_generated", []),
        download_urls=task.get("download_urls", []),
        metadata=task.get("metadata", {})
    )

async def _generate_docs_background(
    session_id: str,
    project_name: str,
    include_examples: bool
):
    """
    Background task for documentation generation
    Updates progress in generation_tasks
    """
    from backend.routes.upload import active_sessions
    from backend.services.task_scheduler import AgentStage  # ✅ Import AgentStage enum
    
    try:
        task = generation_tasks[session_id]
        session_info = active_sessions[session_id]
        session_dir = Path(session_info["session_dir"])
        
        # Stage 1: Create chunks
        task.update({
            "status": TaskStatus.PROCESSING,
            "progress": 10,
            "current_stage": "Analyzing files",
            "message": "Creating intelligent file chunks..."
        })
        
        files_metadata = [chunker.extract_metadata(Path(f["path"])) for f in session_info["files"]]
        chunks = chunker.create_chunks(files_metadata)
        print(f"📦 Created {len(chunks)} chunks from {len(files_metadata)} files")
        
        # Stage 2: Run agents
        task.update({
            "status": TaskStatus.ANALYZING,
            "progress": 30,
            "current_stage": "Running AI agents",
            "message": f"Processing {len(chunks)} chunks with parallel agents..."
        })
        
        coordinator = AgentCoordinator()
        agent_results = await coordinator.coordinate({
            "chunks": chunks,
            "project_name": project_name,
            "session_id": session_id,
            "include_examples": include_examples
        })
        
        # Stage 3: Save outputs - ✅ FIXED: Use AgentStage enum keys directly
        task.update({
            "status": TaskStatus.DOCUMENTING,
            "progress": 80,
            "current_stage": "Generating documents",
            "message": "Saving documentation files..."
        })
        
        output_dir = settings.OUTPUT_DIR / session_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        files_generated = []
        download_urls = []
        
        # ✅ FIXED: Save README using AgentStage enum
        readme_result = agent_results.get(AgentStage.README)
        if readme_result and "readme_content" in readme_result:
            readme_path = output_dir / "README.md"
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_result["readme_content"])
            files_generated.append(str(readme_path))
            download_urls.append(f"/api/download/{session_id}/README.md")
            print(f"✅ Saved: {readme_path}")
        
        # ✅ FIXED: Save API Reference using AgentStage enum
        api_result = agent_results.get(AgentStage.API_DOCS)
        if api_result and "api_reference" in api_result:
            api_path = output_dir / "API_REFERENCE.md"
            with open(api_path, 'w', encoding='utf-8') as f:
                f.write(api_result["api_reference"])
            files_generated.append(str(api_path))
            download_urls.append(f"/api/download/{session_id}/API_REFERENCE.md")
            print(f"✅ Saved: {api_path}")
            
            # Also save examples if available
            if "examples" in api_result:
                examples_path = output_dir / "EXAMPLES.md"
                with open(examples_path, 'w', encoding='utf-8') as f:
                    f.write(api_result["examples"])
                files_generated.append(str(examples_path))
                download_urls.append(f"/api/download/{session_id}/EXAMPLES.md")
                print(f"✅ Saved: {examples_path}")
        
        # ✅ FIXED: Save Architecture docs using AgentStage enum
        analysis_result = agent_results.get(AgentStage.ANALYSIS)
        if analysis_result:
            arch_path = output_dir / "ARCHITECTURE.md"
            arch_content = f"""# Architecture Documentation

## Overview
{analysis_result.get('architecture_overview', 'N/A')}

## Component Analysis
{analysis_result.get('component_analysis', 'N/A')}

## Technology Stack
{analysis_result.get('tech_stack', 'N/A')}

## Dependencies
{analysis_result.get('dependencies', 'N/A')}

## Design Patterns
{analysis_result.get('key_patterns', 'N/A')}
"""
            with open(arch_path, 'w', encoding='utf-8') as f:
                f.write(arch_content)
            files_generated.append(str(arch_path))
            download_urls.append(f"/api/download/{session_id}/ARCHITECTURE.md")
            print(f"✅ Saved: {arch_path}")
        
        print(f"📄 Generated {len(files_generated)} files in {output_dir}")
        
        # Complete
        task.update({
            "status": TaskStatus.COMPLETED,
            "progress": 100,
            "current_stage": "Complete",
            "message": f"Generated {len(files_generated)} documentation files",
            "files_generated": files_generated,
            "download_urls": download_urls,
            "metadata": {
                "project_name": project_name,
                "files_analyzed": len(files_metadata),
                "chunks_processed": len(chunks),
                "agents_used": 3
            }
        })
        print(f"✅ Documentation generation complete for {session_id}")
        
    except Exception as e:
        print(f"❌ Generation failed for {session_id}: {str(e)}")
        import traceback
        traceback.print_exc()  # Print full error for debugging
        generation_tasks[session_id].update({
            "status": TaskStatus.FAILED,
            "progress": 0,
            "current_stage": "Error",
            "message": f"Generation failed: {str(e)}"
        })