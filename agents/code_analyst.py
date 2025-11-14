"""
Code Analyst Agent - Stage 1: Analyzes code structure
"""
from typing import Dict, List
from agents.base_agent import BaseAgent

class CodeAnalystAgent(BaseAgent):
    """
    Analyzes code structure, dependencies, and architecture
    Processes chunks incrementally to handle large codebases
    """
    
    def __init__(self):
        super().__init__(
            role="Senior Code Architect & Analyst",
            goal="Analyze code structure, identify patterns, and create comprehensive architecture overview",
            backstory="""You are an expert software architect with 15+ years of experience.
            You can quickly understand large codebases, identify architectural patterns,
            trace dependencies, and explain complex systems in clear terms.
            You excel at creating high-level overviews from code summaries."""
        )
    
    async def execute(self, input_data: Dict, context: Dict) -> Dict:
        """
        Execute code analysis across all chunks
        
        Args:
            input_data: {
                "chunks": List of file chunks,
                "project_name": Project name,
                "session_id": Session identifier
            }
            context: Results from previous agents (empty for first agent)
        
        Returns:
            {
                "architecture_overview": High-level architecture,
                "component_analysis": Detailed component breakdown,
                "dependencies": Dependency graph,
                "tech_stack": Technologies used,
                "key_patterns": Design patterns identified
            }
        """
        chunks = input_data.get("chunks", [])
        project_name = input_data.get("project_name", "Project")
        
        print(f"📊 Analyzing {len(chunks)} chunk(s) of code...")
        
        # Stage 1: Analyze each chunk
        chunk_analyses = []
        for i, chunk in enumerate(chunks):
            print(f"  🔍 Analyzing chunk {i+1}/{len(chunks)}...")
            analysis = await self._analyze_chunk(chunk, i)
            chunk_analyses.append(analysis)
        
        # Stage 2: Synthesize overall architecture
        print("  🏗️ Synthesizing architecture overview...")
        architecture = await self._synthesize_architecture(chunk_analyses, project_name)
        
        return {
            "architecture_overview": architecture["overview"],
            "component_analysis": architecture["components"],
            "dependencies": architecture["dependencies"],
            "tech_stack": architecture["tech_stack"],
            "key_patterns": architecture["patterns"],
            "file_structure": architecture["structure"]
        }
    
    async def _analyze_chunk(self, chunk: List[Dict], chunk_idx: int) -> str:
        """Analyze a single chunk of files"""
        
        # Prepare chunk summary
        summary = f"## Chunk {chunk_idx + 1}\n\n"
        for file_meta in chunk:
            summary += f"### {file_meta['name']}\n"
            summary += f"- Path: {file_meta['path']}\n"
            summary += f"- Lines: {file_meta.get('lines', 0)}\n"
            
            if file_meta.get('functions'):
                summary += f"- Functions: {', '.join(file_meta['functions'][:10])}\n"
            if file_meta.get('classes'):
                summary += f"- Classes: {', '.join(file_meta['classes'][:10])}\n"
            
            if file_meta.get('preview'):
                summary += f"\n**Code Preview:**\n``````\n\n"
        
        # Analyze chunk
        prompt = f"""Analyze this code chunk and provide:

{summary}

Provide a concise analysis including:
1. Purpose of these files
2. Key components and their responsibilities
3. Technologies/frameworks used
4. Notable patterns or structures

Keep response under 500 words."""
        
        return await self._generate(prompt)
    
    async def _synthesize_architecture(self, chunk_analyses: List[str], project_name: str) -> Dict:
        """Synthesize overall architecture from chunk analyses"""
        
        combined_analysis = "\n\n".join([
            f"## Analysis Part {i+1}\n{analysis}"
            for i, analysis in enumerate(chunk_analyses)
        ])
        
        prompt = f"""Based on these code analyses for "{project_name}":

{combined_analysis}

Create a comprehensive architecture document with:

## 1. ARCHITECTURE OVERVIEW
High-level description of the system architecture, main components, and how they interact.

## 2. COMPONENT BREAKDOWN
Detailed breakdown of each major component/module, its purpose, and key responsibilities.

## 3. TECHNOLOGY STACK
List of technologies, frameworks, and libraries used with their purposes.

## 4. DEPENDENCIES & INTERACTIONS
How components interact, data flows, and external dependencies.

## 5. DESIGN PATTERNS
Architectural and design patterns identified in the codebase.

## 6. FILE STRUCTURE
Logical organization of files and folders.

Format in clear Markdown with proper headers."""
        
        architecture_doc = await self._generate(prompt)
        
        # Parse into structured format
        return {
            "overview": self._extract_section(architecture_doc, "ARCHITECTURE OVERVIEW"),
            "components": self._extract_section(architecture_doc, "COMPONENT BREAKDOWN"),
            "tech_stack": self._extract_section(architecture_doc, "TECHNOLOGY STACK"),
            "dependencies": self._extract_section(architecture_doc, "DEPENDENCIES"),
            "patterns": self._extract_section(architecture_doc, "DESIGN PATTERNS"),
            "structure": self._extract_section(architecture_doc, "FILE STRUCTURE")
        }
    
    def _extract_section(self, text: str, header: str) -> str:
        """Extract section from markdown document"""
        lines = text.split('\n')
        section_lines = []
        capture = False
        
        for line in lines:
            if header.upper() in line.upper():
                capture = True
                continue
            elif capture and line.startswith('##'):
                break
            elif capture:
                section_lines.append(line)
        
        return '\n'.join(section_lines).strip()
