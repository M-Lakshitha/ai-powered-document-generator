"""
Intelligent code chunking with token awareness
"""
import tiktoken
import ast
from pathlib import Path
from typing import List, Dict
from backend.config import settings

class SmartChunker:
    """Chunks code files to fit LLM context windows"""
    
    def __init__(self):
        self.max_tokens = settings.MAX_CHUNK_TOKENS
        self.encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoder.encode(text))
    
    def extract_metadata(self, filepath: Path) -> Dict:
        """Extract metadata from code file"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            tokens = self.count_tokens(content)
            lines = len(content.splitlines())
            
            # Extract structure for Python files
            functions, classes = [], []
            if filepath.suffix == '.py':
                try:
                    tree = ast.parse(content)
                    functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                    classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
                except:
                    pass
            
            # Create smart preview (prioritize docstrings and definitions)
            preview = self._create_smart_preview(content, filepath.suffix)
            
            return {
                "path": str(filepath),
                "name": filepath.name,
                "extension": filepath.suffix,
                "size": len(content),
                "tokens": tokens,
                "lines": lines,
                "functions": functions,
                "classes": classes,
                "preview": preview,
                "full_content": content if tokens < 1500 else None
            }
        
        except Exception as e:
            return {
                "path": str(filepath),
                "name": filepath.name,
                "error": str(e)
            }
    
    def _create_smart_preview(self, content: str, extension: str, max_lines: int = 30) -> str:
        """Create intelligent preview focusing on important parts"""
        lines = content.split('\n')
        
        # Priority lines (comments, docstrings, function defs, class defs)
        priority_keywords = ['def ', 'class ', '"""', "'''", '//', '/*', '#', 'function ', 'const ', 'interface ']
        
        important_lines = []
        for i, line in enumerate(lines[:100]):  # Check first 100 lines
            if any(keyword in line for keyword in priority_keywords):
                # Include line and next 2 lines (for docstrings)
                important_lines.extend(lines[i:min(i+3, len(lines))])
                if len(important_lines) >= max_lines:
                    break
        
        preview = '\n'.join(important_lines[:max_lines])
        if len(lines) > max_lines:
            preview += f"\n... ({len(lines) - max_lines} more lines)"
        
        return preview
    
    def create_chunks(self, files_metadata: List[Dict]) -> List[List[Dict]]:
        """Group files into token-aware chunks"""
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for file_meta in files_metadata:
            if 'error' in file_meta:
                continue
            
            file_tokens = file_meta['tokens']
            
            # Create summary for this file (lighter than full content)
            summary_tokens = self.count_tokens(self._create_file_summary(file_meta))
            
            if current_tokens + summary_tokens > self.max_tokens:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = [file_meta]
                current_tokens = summary_tokens
            else:
                current_chunk.append(file_meta)
                current_tokens += summary_tokens
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _create_file_summary(self, file_meta: Dict) -> str:
        """Create concise file summary"""
        summary = f"## {file_meta['name']}\n\n"
        summary += f"- Path: {file_meta['path']}\n"
        summary += f"- Lines: {file_meta['lines']}\n"
        summary += f"- Size: {file_meta['size']} bytes\n\n"
        
        if file_meta.get('functions'):
            summary += f"**Functions**: {', '.join(file_meta['functions'][:15])}\n\n"
        
        if file_meta.get('classes'):
            summary += f"**Classes**: {', '.join(file_meta['classes'][:10])}\n\n"
        
        if file_meta.get('preview'):
            summary += f"**Code Preview**:\n``````\n\n"
        
        return summary

# Global instance
chunker = SmartChunker()
