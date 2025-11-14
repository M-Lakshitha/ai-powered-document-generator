from typing import Dict
from agents.base_agent import BaseAgent


class READMECreatorAgent(BaseAgent):
    """
    Creates professional README files
    Runs in parallel with API documentation
    """
    
    def __init__(self):
        super().__init__(
            role="README Specialist & Project Documentation Expert",
            goal="Create engaging, professional README files that make projects successful",
            backstory="""You create README files for top open-source projects.
You know exactly what makes a great README:
- Clear, compelling project description
- Easy-to-follow installation instructions
- Practical quick start guides
- Beautiful formatting and structure
- Helpful badges and screenshots
- Contributing guidelines that encourage participation

Your READMEs help projects get stars, users, and contributors."""
        )
    
    async def execute(self, input_data: Dict, context: Dict) -> Dict:
        """
        Generate README.md based on code analysis
        
        Args:
            input_data: Original input data
            context: {
                "AgentStage.ANALYSIS": Results from CodeAnalystAgent
            }
        
        Returns:
            {
                "readme_content": Complete README.md content,
                "badges": Suggested badges,
                "screenshots": Screenshot placeholders
            }
        """
        from backend.services.task_scheduler import AgentStage
        
        analysis = context.get(AgentStage.ANALYSIS, {})
        project_name = input_data.get("project_name", "Project")
        
        print("📄 Creating README.md...")
        
        readme = await self._generate_readme(
            project_name,
            analysis.get("architecture_overview", ""),
            analysis.get("tech_stack", ""),
            analysis.get("component_analysis", "")
        )
        
        return {
            "readme_content": readme,
            "badges": self._generate_badges(analysis.get("tech_stack", "")),
            "screenshots": self._generate_screenshot_placeholders()
        }
    
    async def _generate_readme(
        self,
        project_name: str,
        overview: str,
        tech_stack: str,
        components: str
    ) -> str:
        """Generate complete README"""
        prompt = f"""Create a professional README.md for "{project_name}":

## Architecture
{overview}

## Technologies
{tech_stack}

## Components
{components[:500]}

Create a README with these sections:

# {project_name}
> One-sentence tagline describing the project

## 🌟 Features
- Key feature 1
- Key feature 2
- Key feature 3

## 🚀 Quick Start

### Prerequisites
List requirements

### Installation
```bash
# Installation commands
```

### Usage
```bash
# Usage examples
```

## 📖 Documentation
Link to full documentation

## 🤝 Contributing
How to contribute

## 📄 License
License information

## 📧 Contact
Contact information

Make it engaging, professional, and easy to follow!"""

        result = await self.llm_call(prompt)
        return result
    
    def _generate_badges(self, tech_stack: str) -> str:
        """Generate markdown badges based on tech stack"""
        badges = []
        tech_lower = tech_stack.lower()
        
        # Language badges
        if 'python' in tech_lower:
            badges.append('![Python](https://img.shields.io/badge/python-3.9+-blue.svg)')
        if 'javascript' in tech_lower or 'node' in tech_lower:
            badges.append('![JavaScript](https://img.shields.io/badge/javascript-ES6+-yellow.svg)')
        if 'typescript' in tech_lower:
            badges.append('![TypeScript](https://img.shields.io/badge/typescript-4.0+-blue.svg)')
        
        # Framework badges
        if 'react' in tech_lower:
            badges.append('![React](https://img.shields.io/badge/react-18+-blue.svg)')
        if 'fastapi' in tech_lower:
            badges.append('![FastAPI](https://img.shields.io/badge/fastapi-0.100+-green.svg)')
        if 'flask' in tech_lower:
            badges.append('![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)')
        if 'django' in tech_lower:
            badges.append('![Django](https://img.shields.io/badge/django-4.0+-green.svg)')
        if 'vue' in tech_lower:
            badges.append('![Vue](https://img.shields.io/badge/vue-3.0+-green.svg)')
        if 'angular' in tech_lower:
            badges.append('![Angular](https://img.shields.io/badge/angular-14+-red.svg)')
        if 'nextjs' in tech_lower or 'next.js' in tech_lower:
            badges.append('![Next.js](https://img.shields.io/badge/next.js-13+-black.svg)')
        
        # Database badges
        if 'postgres' in tech_lower or 'postgresql' in tech_lower:
            badges.append('![PostgreSQL](https://img.shields.io/badge/postgresql-14+-blue.svg)')
        if 'mysql' in tech_lower:
            badges.append('![MySQL](https://img.shields.io/badge/mysql-8.0+-blue.svg)')
        if 'mongodb' in tech_lower:
            badges.append('![MongoDB](https://img.shields.io/badge/mongodb-5.0+-green.svg)')
        if 'redis' in tech_lower:
            badges.append('![Redis](https://img.shields.io/badge/redis-7.0+-red.svg)')
        
        # Cloud/DevOps badges
        if 'docker' in tech_lower:
            badges.append('![Docker](https://img.shields.io/badge/docker-enabled-blue.svg)')
        if 'kubernetes' in tech_lower or 'k8s' in tech_lower:
            badges.append('![Kubernetes](https://img.shields.io/badge/kubernetes-ready-blue.svg)')
        if 'aws' in tech_lower:
            badges.append('![AWS](https://img.shields.io/badge/aws-deployed-orange.svg)')
        if 'azure' in tech_lower:
            badges.append('![Azure](https://img.shields.io/badge/azure-deployed-blue.svg)')
        if 'gcp' in tech_lower or 'google cloud' in tech_lower:
            badges.append('![GCP](https://img.shields.io/badge/gcp-deployed-blue.svg)')
        
        # Testing badges
        if 'pytest' in tech_lower:
            badges.append('![Pytest](https://img.shields.io/badge/pytest-enabled-green.svg)')
        if 'jest' in tech_lower:
            badges.append('![Jest](https://img.shields.io/badge/jest-enabled-green.svg)')
        
        # Common badges (always include)
        badges.append('![License](https://img.shields.io/badge/license-MIT-blue.svg)')
        badges.append('![Maintenance](https://img.shields.io/badge/maintained-yes-green.svg)')
        
        return '\n'.join(badges) if badges else '![License](https://img.shields.io/badge/license-MIT-blue.svg)'
    
    def _generate_screenshot_placeholders(self) -> str:
        """Generate screenshot placeholders"""
        return """## 📸 Screenshots

<!-- Add your screenshots here -->
![Screenshot 1](docs/screenshots/screenshot1.png)
*Caption for screenshot 1*

![Screenshot 2](docs/screenshots/screenshot2.png)
*Caption for screenshot 2*

![Screenshot 3](docs/screenshots/screenshot3.png)
*Caption for screenshot 3*"""