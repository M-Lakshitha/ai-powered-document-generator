from typing import Dict
from agents.base_agent import BaseAgent

class APIDocumenterAgent(BaseAgent):
    """
    Creates comprehensive API documentation
    Runs in parallel with README creation
    """
    
    def __init__(self):
        super().__init__(
            role="Senior API Documentation Engineer",
            goal="Create clear, comprehensive API documentation with examples and best practices",
            backstory="""You are an expert technical writer specializing in API documentation.
You follow Google's documentation style guide and always include:
- Clear descriptions of purpose and usage
- Complete parameter documentation with types
- Return value specifications
- Practical usage examples
- Error handling and edge cases
- Best practices and common pitfalls

Your documentation helps developers integrate quickly and correctly."""
        )
    
    async def execute(self, input_data: Dict, context: Dict) -> Dict:
        """
        Generate API documentation based on code analysis
        
        Args:
            input_data: Original input data
            context: {
                "AgentStage.ANALYSIS": Results from CodeAnalystAgent
            }
        
        Returns:
            {
                "api_reference": Complete API reference documentation,
                "examples": Usage examples,
                "quick_reference": Quick reference guide
            }
        """
        from backend.services.task_scheduler import AgentStage
        
        # Get analysis from previous agent
        analysis = context.get(AgentStage.ANALYSIS, {})
        
        print("📝 Generating API documentation...")
        
        # Generate main API docs
        api_docs = await self._generate_api_reference(
            analysis.get("component_analysis", ""),
            analysis.get("architecture_overview", "")
        )
        
        # Generate usage examples
        examples = await self._generate_examples(api_docs)
        
        return {
            "api_reference": api_docs,
            "examples": examples,
            "quick_reference": self._create_quick_reference(api_docs)
        }
    
    async def _generate_api_reference(self, components: str, overview: str) -> str:
        """Generate detailed API reference"""
        prompt = f"""Create comprehensive API documentation based on this analysis:

## Architecture Overview
{overview}

## Components
{components}

Generate API documentation in this format:

# API Reference

## [Component/Module Name]

### ClassName or FunctionName

**Description**
Clear description of what it does and when to use it.

**Parameters**
- `param_name` (type): Description of parameter
- `param_name2` (type, optional): Description with default value

**Returns**
- type: Description of return value

**Raises**
- ExceptionType: When this exception is raised

**Example**
```python
# Code example showing usage
```

**Notes**
- Important considerations
- Common pitfalls to avoid

Include all functions, classes, and methods found in the code."""

        result = await self.llm_call(prompt)
        return result
    
    async def _generate_examples(self, api_docs: str) -> str:
        """Generate practical usage examples"""
        prompt = f"""Based on this API documentation:

{api_docs}

Create a comprehensive USAGE EXAMPLES section with:

1. **Quick Start Example**: Simplest possible usage
2. **Common Use Cases**: 3-5 real-world scenarios
3. **Advanced Examples**: Complex usage patterns
4. **Best Practices**: Recommended patterns and anti-patterns

Format as:

# Usage Examples

## Quick Start
```python
# Minimal example to get started
```

## Common Use Cases

### Use Case 1: [Title]
```python
# Example code
```

### Use Case 2: [Title]
```python
# Example code
```

## Advanced Usage
```python
# Complex example
```

## Best Practices
- ✅ DO: Recommended approach
- ❌ DON'T: Anti-pattern to avoid
"""

        result = await self.llm_call(prompt)
        return result
    
    def _create_quick_reference(self, api_docs: str) -> str:
        """Create a quick reference cheat sheet"""
        # Extract key information for quick reference
        lines = api_docs.split('\n')
        quick_ref = ["# Quick Reference\n\n"]
        
        current_section = None
        for line in lines:
            # Capture main sections and function signatures
            if line.startswith('### '):
                quick_ref.append(f"\n{line}\n")
            elif line.startswith('- `') and '(' in line:
                quick_ref.append(line + "\n")
        
        return ''.join(quick_ref)